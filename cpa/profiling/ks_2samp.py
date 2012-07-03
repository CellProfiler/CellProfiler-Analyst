# New ks_2samp version submitted to scipy (see
# https://github.com/scipy/scipy/pull/8).

import numpy as np
from numpy import asarray
from scipy.stats import ksprob

def ks_2samp(data1, data2, signed=False):
    """
    Computes the Kolmogorov-Smirnov statistic on two samples, as well
    as its two-sided p-value.

    The two-sample Kolmogorov-Smirnov statistic is 

        D = sup_x |A(x) - B(x)|,

    where A and B are the empirical distribution functions of
    parameters `a` and `b`, respectively. This is a two-sided test for
    the null hypothesis that two independent samples are drawn from the
    same continuous distribution.

    Parameters
    ----------
    a, b : sequence of 1-D ndarrays
        Two arrays of sample observations assumed to be drawn from a continuous
        distribution. The sample sizes can be different.
    signed : {False, True}, optional
        This flag determines whether the returned value `D` should 
        be signed to indicate which distribution function is largest 
        at the point where the two distribution functions differ the most.
        When `signed` is true, `D` will be

            A(x) - B(x)   where   x = arg sup_x |A(x) - B(x)|.

        With the default value, False, `D` will be sup_x |A(X) - B(x)|
        and therefore always in [0, 1].

    Returns
    -------
    D : float
        KS statistic
    p-value : float
        two-tailed p-value


    Notes
    -----

    This tests whether 2 samples are drawn from the same distribution. Note
    that, like in the case of the one-sample K-S test, the distribution is
    assumed to be continuous.

    This is the two-sided test, one-sided tests are not implemented.
    The test uses the two-sided asymptotic Kolmogorov-Smirnov distribution.

    If the K-S statistic is small or the p-value is high, then we cannot
    reject the hypothesis that the distributions of the two samples
    are the same.

    Examples
    --------

    >>> from scipy import stats
    >>> import numpy as np
    >>> from scipy.stats import ks_2samp

    >>> #fix random seed to get the same result
    >>> np.random.seed(12345678);

    >>> n1 = 200  # size of first sample
    >>> n2 = 300  # size of second sample

    different distribution
    we can reject the null hypothesis since the pvalue is below 1%

    >>> rvs1 = stats.norm.rvs(size=n1,loc=0.,scale=1);
    >>> rvs2 = stats.norm.rvs(size=n2,loc=0.5,scale=1.5)
    >>> ks_2samp(rvs1,rvs2)
    (0.20833333333333337, 4.6674975515806989e-005)

    slightly different distribution
    we cannot reject the null hypothesis at a 10% or lower alpha since
    the pvalue at 0.144 is higher than 10%

    >>> rvs3 = stats.norm.rvs(size=n2,loc=0.01,scale=1.0)
    >>> ks_2samp(rvs1,rvs3)
    (0.10333333333333333, 0.14498781825751686)

    identical distribution
    we cannot reject the null hypothesis since the pvalue is high, 41%

    >>> rvs4 = stats.norm.rvs(size=n2,loc=0.0,scale=1.0)
    >>> ks_2samp(rvs1,rvs4)
    (0.07999999999999996, 0.41126949729859719)

    When `signed` is true, the KS-statistic will be negative if the
    second distribution function is the largest at the point where the
    distribution functions differ the most.

    >>> ks_2samp(rvs1,rvs4,signed=True)
    (-0.07999999999999996, 0.41126949729859719)

    """
    data1, data2 = map(asarray, (data1, data2))
    n1 = data1.shape[0]
    n2 = data2.shape[0]
    n1 = len(data1)
    n2 = len(data2)
    data1 = np.sort(data1)
    data2 = np.sort(data2)
    data_all = np.concatenate([data1,data2])
    cdf1 = np.searchsorted(data1,data_all,side='right')/(1.0*n1)
    cdf2 = (np.searchsorted(data2,data_all,side='right'))/(1.0*n2)
    diff = cdf1-cdf2
    ind = np.argmax(np.absolute(diff))
    d = diff[ind]
    absd = np.absolute(d)
    en = np.sqrt(n1*n2/float(n1+n2))
    try:
        prob = ksprob((en+0.12+0.11/en)*absd)
    except:
        prob = 1.0
    if signed:
        return d, prob
    else:
        return absd, prob
