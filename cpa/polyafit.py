
from numpy import *
from scipy.integrate import fixed_quad
from scipy.special import gammaln, betaln, digamma, polygamma
from scipy.optimize import fmin
import sys

def lnchoose(n, m):
    nf = gammaln(n + 1)
    mf = gammaln(m + 1)
    nmmnf = gammaln(n - m + 1)
    return nf - (mf + nmmnf)


def logP(alpha, counts):
    alphasum = sum(alpha)
    def logPsingle(c):
        return gammaln(alphasum) - gammaln(alphasum + sum(c)) + sum([gammaln(alpha[k] + c[k]) - gammaln(alpha[k]) for k in range(len(alpha))])
    return sum([logPsingle(counts[i, :]) for i in range(counts.shape[0])])

def dirichlet_moment_match(proportions, weights):
    a = array(average(proportions, axis=0, weights=weights.flat))
    m2 = array(average(multiply(proportions, proportions), axis=0, weights=weights.flat))
    nz = (a > 0)
    aok = a[nz]
    m2ok = m2[nz]
    s = median((aok - m2ok) / (m2ok - aok * aok))
    return matrix(a * s)
    


def polya_moment_match(counts):
    return dirichlet_moment_match(array(counts) / sum(counts, axis=1).repeat(counts.shape[1], axis=1), sum(counts, axis=1))

def fit_betabinom_minka(counts, maxiter=1000, tol=1e-6, initial_guess=None):
    ''' See Estimating a Dirichlet Distribution, Thomas P. Minka, 2003,
    eq. 55.  see also the code for polya_fit_simple.m in his fastfit
    matlab toolbox, which this code is a translation of.

    counts should be NxK with N samples over K classes.'''

    counts = matrix(counts).astype(float)
    
    # remove observations with no trials
    counts = counts[sum(counts.A, axis=1) > 0, :]
    if initial_guess == None:
        alpha = polya_moment_match(counts).T
    else:
        alpha = matrix(initial_guess).T

    # Abstraction barrier: now in Dirichlet/Polya mode, following naming in Minka's paper.
    n = counts.T
    N = n.shape[1]
    n_i = n.sum(axis=0)

    change = 2*tol
    iter = 0
    while (change > tol) and (iter < maxiter):
        numerator = digamma(n + alpha.repeat(N, axis=1)).sum(axis=1) - N * digamma(alpha)
        denominator = digamma(n_i + alpha.sum()).sum() - N * digamma(alpha.sum())
        old_alpha = alpha
        alpha = multiply(alpha, numerator / denominator)
        change = abs(old_alpha - alpha).max()
        iter = iter + 1

    # now leaving Abstraction Barrier

    return array(alpha[:,0]).T, iter < maxiter

def di_pochhammer(x, n):
    'digamma(x+n) - digamma(x), but 0 for n = 0'
    y = zeros(n.shape)
    nz = (n > 0)
    y[nz] = digamma(x + n[nz]) - digamma(x)
    return y

def trigamma(x):
    return polygamma(1, x)

def tri_pochhammer(x, n):
    'trigamma(x+n) - trigamma(x), but 0 for n = 0'
    y = zeros(n.shape)
    nz = (n > 0)
    y[nz] = trigamma(x + n[nz]) - trigamma(x)
    return y
    
    

def polya_fit_m(counts, alpha, tol):
    '''see polya_fit_m.m in fastfit toolbox,
    and equation (118) fot Minka, 2003.'''
    s = sum(alpha)
    m = alpha / s
    N, K = counts.shape
    for iter in range(20):
        old_m = m.copy()
        a = s * m
        for k in range(K):
            dk = counts[:, k]
            vdk = a[k] * di_pochhammer(a[k], dk)
            m[k] = sum(vdk)
        m =  m / sum(m)
        if abs(m - old_m).max() < tol:
            break
    return s * m

def quad_root(a, b, c):
    '''roots of a^2 x + b x + c'''
    top = sqrt(b**2 - 4*a*c)
    return max(((-b + top) / (2 * a), (-b - top) / (2 * a)))

def polya_fit_s(counts, alpha, tol):
    '''see polya_fit_s.m in fastfit toolbox.  This implements section
    4.2 from Minka, 2003.  I've tried to translate it into the symbols
    of the paper.'''
    s = sum(alpha)
    m = alpha / s
    N, K = counts.shape
    scounts = sum(counts, axis=1)

    def s_derivatives(alpha_temp):
        s = sum(alpha_temp)
        m = alpha_temp / s
        g = -sum(di_pochhammer(s, scounts)) # eq 81, first part
        h = -sum(tri_pochhammer(s, scounts)) # eq 82, first part
        for k in range(K):
            dk = counts[:,k]
            g += m[k] * sum(di_pochhammer(alpha_temp[k], dk)) # eq 81, second part
            h += m[k]**2 * sum(tri_pochhammer(alpha_temp[k], dk)) # eq 82, second part
        return g, h

    def stable_a2(alpha_temp):
        m = alpha_temp / sum(alpha_temp)
        a = sum(scounts * (scounts - 1) * (2 * scounts - 1)) / 6.0
        for k in range(K):
            dk = counts[:,k]
            ak = sum(dk * (dk - 1) * (2 * dk - 1)) / 6.0
            if ak > 0:
                a -= ak / m[k]**2
        return a

    eps = finfo(float64).eps
    # minka has 10 iters for s, compared to 20 for m.  perhaps because s takes longer.
    for iter in range(10): 
        g, h = s_derivatives(alpha)
        if g > eps:
            c = g + s * h # eq 86
            if c >= 0:
                s = inf # comment after eq 87
            else:
                s = s / (1 + g / (h * s)) # eq 87
        elif g < -eps:
            c = sum(counts > 0) - sum(scounts > 0) # eq 94
            if c > 0:
                a0 = s**2 * h + c # eq 99
                a1 = 2 * s**2 * (s * h + g) # eq 98
                if abs(2 * g + h * s) > eps:
                    a2 = s**3 * (2 * g + h * s) # eq 97
                else:
                    a2 = stable_a2(alpha) # eq 92
                b = quad_root(a2, a1, a0) # eq 96 (disagreement with polya_fit_s.m in fastfit)
                s = 1 / ((1 / s) - (g / c) * ((s + b) / b)**2) # eq 100
        else:
            pass # no update
        old_alpha = alpha
        alpha = s * m
        if abs(alpha - old_alpha).max() < tol:
            break

    return alpha

                



def fit_betabinom_minka_alternating(counts, maxiter=1000, tol=1e-6):
    ''' See Estimating a Dirichlet Distribution, Thomas P. Minka, 2003.
    See also the code for polya_fit_ms.m in his fastfit
    matlab toolbox, which this code is a translation of.

    counts should be NxK with N samples over K classes.'''

    counts = matrix(counts).astype(float)
    # remove observations with no trials
    counts = counts[sum(counts.A, axis=1) > 0, :]
    alpha = array(polya_moment_match(counts)).flatten()
    counts = counts.A

    change = 2 * tol
    iter = 0
    while (change > tol) and (iter < maxiter):
        old_alpha = alpha
        alpha = polya_fit_m(counts, alpha, tol)
        alpha = polya_fit_s(counts, alpha, tol)
        change = abs(old_alpha - alpha).max()
        iter += 1
    return alpha, iter < maxiter


    
def fit_to_data_infile(fname):
    import sys
    f = open(fname)
    data = loadtxt(f).astype(int32)
    wells = {}
    for l in data:
        wellidx = (l[1] - 1) // 4
        wells[wellidx] = l[2:] + wells.get(wellidx, array([0,0,0]))
    test = array(list(wells.values()))
    atest = fit_betabinom_minka_alternating(test, maxiter=3000)
    aver = fit_betabinom_minka(test, maxiter=3000, initial_guess=atest[0])
    return aver[0].flatten(), aver[1], array(list(wells.keys())), array(list(wells.values()))
    

if __name__ == '__main__':
    print((fit_to_data_infile('PBscores.txt')[0]))
