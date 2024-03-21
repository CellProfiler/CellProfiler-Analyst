
# CellProfiler is distributed under the GNU General Public License,
# but this file is licensed under the more permissive BSD license.
# See the accompanying file LICENSE for details.

from numpy import *
from scipy.integrate import quadrature, romberg, fixed_quad
from scipy.special import gammaln, betaln, digamma, polygamma, betainc, gamma
import pdb
from .hypergeom import hyper3F2regularizedZ1, hyper3F2Z1, hyper3F2aZ1


def dirichlet_integrate(alpha):
    normalizer = exp(sum(gammaln(alpha)) - gammaln(sum(alpha)))

    def f_recur(x, idx, upper, vals):
        if idx == 1:
            # base case.
            # set values for last two components
            vals[1] = x
            vals[0] = 1.0 - sum(vals[1:])
            # compute Dirichlet value
            print((vals.T, prod(vals ** (alpha - 1)) , normalizer, alpha))
            return prod(vals.T ** (alpha - 1)) / normalizer
        else:
            vals[idx] = x
            split = alpha[idx-1] / sum(alpha)
            if (split < upper - x):
                return romberg(f_recur, 0, split, args=(idx - 1, upper - x, vals), vec_func=False) + \
                    romberg(f_recur, split, upper - x, args=(idx - 1, upper - x, vals), vec_func=False)
            else:
                return romberg(f_recur, 0, upper - x, args=(idx - 1, upper - x, vals), vec_func=False)

    split = alpha[-1] / sum(alpha)
    print((alpha / sum(alpha)))
    return romberg(f_recur, 0, split, args=(len(alpha) - 1, 1.0, zeros((len(alpha), 1), float64)), vec_func=False) + \
        romberg(f_recur, split, 1, args=(len(alpha) - 1, 1.0, zeros((len(alpha), 1), float64)), vec_func=False) 

def dirichlet_integrate_near0(alpha):
    normalizer = exp(sum(gammaln(alpha)) - gammaln(sum(alpha)))
    K = len(alpha)

    def f_recur(x, idx, vals):
        if idx == K - 2:
            # base case.
            # set values for last two components
            vals[K - 2] = x
            vals[K - 1] = 1.0 - sum(vals[0:K-1])
            # print vals, prod(vals ** (alpha - 1)) / normalizer, normalizer
            for v in vals[1:]:
                assert v <= vals[0]+0.001
            # compute Dirichlet value
            return prod(vals.T ** (alpha - 1)) / normalizer
        else:
            vals[idx] = x
            # we have to fulfill three requirements:
            # vals[i] > 0 for all i
            # vals[0] >= vals[i] for all i 
            # vals[i] sum to 1

            # how much weight is left to assign?
            remaining = 1.0 - sum(vals[:(idx+1)])
            # require vals[i] > 0, and vals[0] >= vals[i]
            lower_bound = max(0.0, remaining - vals[0] * (K - idx - 2))
            upper_bound = min(remaining, vals[0])
            assert lower_bound <= upper_bound+0.001
            v = romberg(f_recur, lower_bound, upper_bound, args=(idx + 1, vals), vec_func=False)
            return v

    return romberg(f_recur, 1.0 / len(alpha), 1, args=(0, zeros((len(alpha), 1), float64)), vec_func=False)

def dirichlet_integrate_zero_enriched(alpha, base_level):
    normalizer = exp(sum(gammaln(alpha)) - gammaln(sum(alpha)))
    K = len(alpha)

    def f_recur(x, idx, vals, remaining):
        if idx == K - 2:
            # base case.
            # set values for last two components
            vals[K - 2] = x
            vals[K - 1] = remaining - x
            # compute Dirichlet value
            return prod(vals.T ** (alpha - 1)) / normalizer
        else:
            vals[idx] = x
            remaining = remaining - x
            v = romberg(f_recur, 0, remaining, args=(idx + 1, vals, remaining), vec_func=False)
            return v

    return romberg(f_recur, base_level, 1, args=(0, zeros((len(alpha), 1), float64), 1.0), vec_func=False)


def integrate_splits(prior, posterior):
    splits = [finfo(float64).eps, 1.0 - finfo(float64).eps, prior[0] / sum(prior), 
              prior[1] / sum(prior), posterior[0] / sum(posterior), 
              posterior[1] / sum (posterior)]
    splits.sort()
    return splits

def integrate(f, splits):
    return sum([romberg(f, lo, hi, vec_func=True, tol=1e-4, divmax=10) for lo, hi in zip(splits[:-1], splits[1:])])

def integrateold(f, splits):
    return sum([fixed_quad(f, lo, hi, n=100)[0] for lo, hi in zip(splits[:-1], splits[1:])])

def pdf_cdf_prod(x, prior, posterior):
    lnCDF = log(betainc(prior[0], prior[1], x))
    lnPDF = (posterior[0] - 1) * log(x) + (posterior[1] - 1) * log(1 - x) - betaln(posterior[0], posterior[1])
    
    return exp(lnCDF + lnPDF)


def beta_enriched(prior, posterior):
    # def f(x):
    #     return beta.cdf(x, prior[0], prior[1]) * beta.pdf(x, posterior[0], posterior[1])
    # def g(x):
    #     return beta.pdf(x, posterior[0], posterior[1])
    # def h(x):
    #     return pdf_cdf_prod(x, prior, posterior)
    # # compute by integration
    # splits = integrate_splits(prior, posterior)
    # v = integrate(f, splits) / integrate(g, splits)
    
    # use closed form
    a = prior[0]
    b = prior[1]
    c = posterior[0]
    d = posterior[1]
    # See Integration.mathetmatica
    # This would be better if we computed the log of the
    # hypergeometric function, but I don't think that's generally
    # possible.
    hyper = hyper3F2aZ1(a, 1-b, a+c, a+c+d)
    scale = exp(gammaln(a) + gammaln(a+c) + gammaln(d) - gammaln(1+a) - gammaln(a+c+d) - betaln(a,b) - betaln(c,d))
    if isnan(hyper * scale):
        # This can happen if hyper and scale are 0 and inf (or vice versa).
        if prior[0] / sum(prior) > posterior[0] / sum(posterior):
            return 0.0
        return 1.0
    return clip(hyper * scale, 0, 1)

def score(prior, counts):
    ''' score a well based on the prior fit to the data and the observed counts '''
    assert prior.shape==counts.shape, "dirichletintegrate.score: array shapes do not match: "+str(prior.shape)+' and '+str(counts.shape)
    K = len(prior)
    posterior = prior + counts
    def score_idx(idx):
        prior_a = prior[idx]
        prior_b = sum(prior) - prior_a
        posterior_a = posterior[idx]
        posterior_b = sum(posterior) - posterior_a
        return beta_enriched((prior_a, prior_b), (posterior_a, posterior_b))
    return [score_idx(i) for i in range(K)]

def logit(p):
     return log2(p) - log2(1-p)

if __name__ == '__main__':
    from .polyafit import fit_to_data_infile
    alpha, converged, wellnums, wellcounts = fit_to_data_infile('PBcounts.txt')
    print(("Fit alpha:", alpha, "\tconverged:", converged))
    for idx, wellnum in enumerate(wellnums):
        print((wellnum, "\t", "\t".join([str(logit(v)) for v in score(alpha, wellcounts[idx])]), "\t", "\t".join([str(v) for v in wellcounts[idx]])))

