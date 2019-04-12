"""
This script contains code to run experiments for semi-supervised learning (SSL) with cause and effect features.
"""


import numpy as np


def sigmoid(x):
    """
    computes the logistic sigmoid function evaluated at input x
    :param x: (n x 1) np.array of reals
    :return: (n x 1) np.array of probabilities
    """

    return 1/(1 + np.exp(-x))


def fy_linear(x, a, b):
    """
    computes the linear function x*W + b , e.g. the logit class probabilities (the input to the sigmoid) from causal features
    :param x: (n x d) np.array of reals - causal features X_C
    :param a: (d x p) weight matrix
    :param b: (1 x p) bias term
    :return: (n x p) np.array of reals
    """

    return np.matmul(x, a) + b


def sample_from_mog(weights, means, covs, n_samples):
    """
    Generates samples from a d-dimensional mixture of Gaussians
    :param weights: (m x 1) np.array - weights of mixture components which have to sum to 1
    :param means: (m x d) np.array of means
    :param covs: (m x d x d) np.array of covariances
    :param n_samples: int number of samples to be drawn
    :return: (n_samples x d) np.array of samples from d-dimensional mixture of Gaussians
    """

    d = means.shape[1]
    comps = np.random.multinomial(1, weights, n_samples)  # (n_samplesxm) mask of components
    sample_means = np.matmul(comps, means)  # (n_samplesxd) matrix of sample means
    sample_covs = np.einsum('ij,jkl->ikl', comps, covs)  # (n_samplesxdxd) tensor of sample variances
    samples = np.zeros((n_samples, d))
    for i in range(n_samples):
        samples[i] = np.random.multivariate_normal(sample_means[i], sample_covs[i])
    return samples


def get_data_linear(weights_c, means_c, covs_c, a_y, b_y, a_e, b_0, b_1, cov_e, n_samples):
    """
    Generates a synthetic data set of size n_samples according to the generative model:

    X_C ~ MoG(weights_c, means_c, covs_c),      X_C is in R^d_c
    Y := I[sigmoid(x_C * a_y + b_y > N_Y],      N_Y ~ U[0,1],       Y is in {0,1}
    X_E := a_e * X_C + b_1*Y + b_0*(1-Y) + N_E,     N_E ~ N(0, cov_e),      X_E is in R^d_e

    :param weights_c: (m x 1) np.array - weights of mixture components which have to sum to 1
    :param means_c: (m x d_c) np.array of means
    :param covs_c: (m x d_c x d_c) np.array of covariances
    :param a_y: (d_c x 1) np.array of weights for logistic regression of Y on X_C
    :param b_y: (1 x 1) bias term for logistic regression of Y on X_C
    :param a_e: (d_c x d_e) np.array of weights for map X_C -> X_E
    :param b_0: (1 x d_e) np.array bias for class Y=0
    :param b_1: (1 x d_e) np.array bias for class Y=1
    :param cov_e: (d_e x d_e) np.array covariance for noise  N_E
    :param n_samples:
    :return: x_c: (n_samples x d_c) np.array of causal features
             y: (n_samples x 1) np.array of class labels
             x_e: (n_samples x d_e) np.array of effect features
    """

    x_c = sample_from_mog(weights_c, means_c, covs_c, n_samples)
    class_probs = sigmoid(fy_linear(x_c, a_y, b_y))  # P(Y=1 | X_C)
    n_y = np.random.uniform(0, 1, (n_samples, 1))
    y = np.ones((n_samples, 1)) * (class_probs > n_y)
    d_e = cov_e[0].shape
    n_e = np.random.multivariate_normal(np.zeros(d_e), cov_e, n_samples)
    x_e = np.matmul(x_c, a_e) + np.matmul(y, b_1) + np.matmul((1-y), b_0) + n_e
    return x_c, y, x_e


m = 3
d_c = 1
d_e = 1
n_samples = 10
weights_c = np.array([.3, .2, .5])
means_c = np.zeros((m, d_c))
covs_c = np.zeros((m, d_c, d_c))
for i in range(m):
    covs_c[i] = np.eye(d_c)
a_y = np.ones((d_c, 1))
b_y = np.ones((1, 1))
a_e = np.ones((d_c, d_e))
b_0 = -2 * np.ones((1, d_e))
b_1 = 2 * np.ones((1, d_e))
cov_e = np.eye(d_e)
x_c, y, x_e = get_data_linear(weights_c, means_c, covs_c, a_y, b_y, a_e, b_0, b_1, cov_e, n_samples)
print(x_c.shape)
print(y.shape)
print(x_e.shape)