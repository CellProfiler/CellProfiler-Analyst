from numpy import *
from scipy.special import erf

def inv_logistic(fracs):
    # only works for all nonzero fractions
    il = log(fracs[:,0] / fracs[:,1])
    il[fracs[:,0] == 0] = min(il[isfinite(il)])
    il[fracs[:,1] == 0] = max(il[isfinite(il)])
    return il.reshape((-1, 1))

def logistic(v):
    return exp(v) / (1 + exp(v))

def posterior_modes(mu, var, n, fracs, muhats, tol=1e-10, maxiter=10, noisy=False):
    '''
    find the conditional posterior modes of samples drawn from N(mu,
    var), given observations in n (total cells) and fracs (fraction
    positive), and initial estimates of the mode in muhats.

    See Ahmed & Xing.
    '''
    for i in range(maxiter):
        # find conditional modes (see Ahmed and Xiu)
        p = logistic(muhats)
        hes = p - p**2
        vhats = 1 / (1 / var + n * hes)
        newmuhats = vhats * (mu / var + n * (hes * muhats + fracs - p))
        if noisy:
            print i, newmuhats, vhats
        if abs(newmuhats - muhats).max() < tol:
            break
        muhats = newmuhats
    return newmuhats, vhats

def score_prob_increase(mu_control, variance_control, mu_treatment, variance_treatment):
    return erf((mu_treatment - mu_control) / sqrt(variance_treatment + variance_control))

def expected_fraction(mu, variance):
    # quick and dirty numerical integration.  logistic is in [0,1] so error is pretty low.
    z = linspace(mu - 4 * variance, mu + 4 * variance, 1000)
    pz = exp(- (z - mu)**2 / (2 * variance))
    pz /= pz.sum()
    return (pz * logistic(z)).sum()

def score_single_phenotype(treatments, counts, control, control_weight=1, tol=1e-10, maxiter=1000):
    '''
    treatments should be an array (it can be of strings).
    counts is Nx2
    control selects which set to use for the baseline distribution.  None indicates use everything.
    control_weight is how many "virtual samples" from the control are used when scoring treatments.

    Returns estimated means, variances, P(Treatment>Control), Expected[fraction positive].
         (as dictionaries from treatment -> value).
    '''

    assert treatments.shape[0] == counts.shape[0]
    assert counts.shape[1] == 2

    treatments = treatments.ravel()
    all_treatments = treatments
    totals = sum(counts, axis=1)

    treatments2 = treatments[totals > 0]
    counts = counts[totals > 0, :]
    totals = totals[totals > 0].reshape((-1, 1))

    # first fit the control distribution
    control_mask = (treatments == control)
    if control is None:
        control_mask[:] = True
    control_counts = counts[control_mask, :].reshape((-1, 2))
    n = totals[control_mask].reshape((-1, 1))
    fracs = control_counts.astype(float) / n
    fracs0 = fracs[:,0].reshape((-1, 1))
    
    muhats = inv_logistic(fracs)
    mu = mean(muhats)
    variance = var(muhats)

    # find mean & variance for controls
    for i in range(maxiter):
        muhats, vhats = posterior_modes(mu, variance, n, fracs0, muhats)
        # update mu, variance from posteriors
        mu, oldmu = mean(muhats), mu
        dvariance = (mu - muhats)**2
        variance, oldvariance = mean(dvariance + vhats), variance
        if (abs(mu - oldmu) < tol) and (abs(variance - oldvariance) < tol):
            break

    out_mus = {}
    out_variances = {}
    out_scores = {}
    out_expected_fracs = {}

    # for each control, find posterior mean & variance, but include
    # control mean/variance weighted by control_weight (in units of
    # number of equivalent samples).
    for t in set(all_treatments):
        n_t = totals[treatments == t]
        counts_t = counts[treatments == t, :]

        num_treatments = n_t.shape[0]
        if num_treatments == 0:
            # nothing to infer from, so just use prior
            out_mus[t] = mu
            out_variances[t] = variance
            continue
        normalizer = 1.0 / (num_treatments + control_weight)

        fracs_t = counts_t.astype(float) / n_t
        fracs0_t = fracs_t[:,0].reshape((-1, 1))
    
        muhats = tile(mu, fracs0_t.shape)
        has_inverse = fracs_t.prod(axis=1) > 0
        if any(has_inverse):
            # this gives a better starting point for highly enriched phenotypes.
            muhats[has_inverse] = (muhats[has_inverse] + inv_logistic(fracs_t[has_inverse, :])) / 2
        mu_t = mu
        variance_t = variance

        # find mean & variance for treatment
        for i in range(maxiter):
            muhats, vhats = posterior_modes(mu_t, variance_t, n_t, fracs0_t, muhats)
            mu_t, oldmu_t = normalizer * (muhats.sum() + control_weight * mu), mu_t
            if isnan(mu_t):
                adsf
            muvariance = (mu_t - muhats)**2
            cvariance = (mu_t - mu)**2
            oldvariance_t = variance_t
            variance_t = normalizer * ((muvariance + vhats).sum() + 
                                       control_weight * (cvariance + variance))
            if (abs(mu_t - oldmu_t) < tol) and (abs(variance_t - oldvariance_t) < tol):
                break
        out_mus[t] = mu_t
        out_variances[t] = variance_t
        out_scores[t] = score_prob_increase(mu, variance, mu_t, variance_t) 
        out_expected_fracs[t] = expected_fraction(mu_t, variance_t)

    return out_mus, out_variances, out_score, out_expected_fracs
