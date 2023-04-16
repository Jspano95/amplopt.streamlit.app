import os
import sys
import streamlit as st
import numpy as np
from amplpy import AMPL, modules
import matplotlib.pyplot as plt
import yfinance as yf
from pypfopt import expected_returns, risk_models
from . import models


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


from apps import INFO_HEADER, INFO_FOOTER


TICKERS = [
    "MSFT",
    "AMZN",
    "KO",
    "MA",
    "COST",
    "LUV",
    "XOM",
    "PFE",
    "JPM",
    "UNH",
    "ACN",
    "DIS",
    "GILD",
    "F",
    "TSLA",
]


@st.cache_data
def load_data(tickers, start, end):
    ohlc = yf.download(tickers, start=start, end=end, period="max")
    prices = ohlc["Adj Close"].dropna(how="all")
    return prices


def main():
    # Logo
    st.image("https://portal.ampl.com/dl/ads/python_ecosystem_badge.png")

    # Time horizon:
    start, end, holdout = "2000-01-01", "2022-12-30", 365

    st.markdown(
        f"""
        # Risk Return

        **A portfolio that gives maximum return for a given risk, or minimum risk for given return is an efficient portfolio.**

        Mean-variance optimization is based on Harry Markowitz’s 1952 paper,
        The key insight is that by combining assets with different **expected
        returns** and **volatilities**, one can decide on a mathematically optimal allocation.

        This method requires expected returns and a risk model (i.e., some way of quantifying asset risk).
        The most commonly-used risk model is the covariance matrix.
        **However, in practice we do not have access to the
        covariance matrix nor to the expected returns.**

        > **NOTE:** We will be using data from **{start}** to **{end}** and we will split it
        > leaving out the last **{holdout}** days for performance validation.
        """
    )

    prices = load_data(TICKERS, start, end)
    past_df, future_df = prices.iloc[:-holdout], prices.iloc[-holdout:]
    risk_methods, return_methods = models.RISK_METHODS, models.RETURN_METHODS

    st.markdown(
        """
        ## Covariance matrix
            
        Risk can be reduced by making many uncorrelated bets and correlation is just normalised covariance.

        **However, we don't have access to covariance for the future data!**

        Estimation of the covariance matrix is a complex task
        so we will use the package [PyPortfolioOpt](https://pyportfolioopt.readthedocs.io/)
        which provides several ways to calculate covariance
        such as semicovariance and exponentially weighted covariance.

        Some methods are provided by [sklearn](https://scikit-learn.org/) but it also
        provides experimental ones such as semicovariance and exponentially weighted covariance.
        """
    )

    risk_method = st.selectbox(
        "Pick the risk method 👇", risk_methods, key="risk_method"
    )

    def plot_matrix(matrix1, matrix2):
        fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2)
        ax1.set_title("Expected covariance")
        ax2.set_title("Real covariance")
        ax1.imshow(matrix1)
        ax2.imshow(matrix2)
        # fig.colorbar(ax1.imshow(matrix1))
        # fig.colorbar(ax2.imshow(matrix2))
        for ax, matrix in [(ax1, matrix1)]:
            ax.set_xticks(np.arange(0, matrix.shape[0], 1))
            ax.set_xticklabels(matrix.index)
            ax.set_yticks(np.arange(0, matrix.shape[0], 1))
            ax.set_yticklabels(matrix.index)
            ax.tick_params("x", labelrotation=90)
        st.pyplot(fig)

    future_cov = risk_models.sample_cov(future_df)
    future_corr = risk_models.cov_to_corr(future_cov)

    S = risk_models.risk_matrix(past_df, method=risk_method)
    plot_matrix(risk_models.cov_to_corr(S), future_corr)

    st.markdown(
        """
    Let's compare the errors for the various methods against the real future cov matrix:
    """
    )

    future_variance = np.diag(future_cov)
    mean_abs_errors = []
    for method in risk_methods:
        S = risk_models.risk_matrix(past_df, method=method)
        variance = np.diag(S)
        mean_abs_errors.append(
            np.sum(np.abs(variance - future_variance)) / len(variance)
        )

    xrange = range(len(mean_abs_errors))
    fig, _ = plt.subplots()
    plt.barh(xrange, mean_abs_errors)
    plt.yticks(xrange, risk_methods)
    st.pyplot(fig)

    st.markdown(
        """
    **Methods that give more weight to recent data, such as exponentially-weighted covariance matrix,
    typically performs better.**
    """
    )

    st.markdown(
        """
    ## Expected returns

    For the expected returns, which we also need,
    [PyPortfolioOpt](https://pyportfolioopt.readthedocs.io/)
    provides several ways to calculate them too:

    - Mean historical return
    - Exponentially weighted mean historical return
    - Capital Asset Pricing Model (CAPM) estimate of returns

    Here is a comparison of mean absolute errors for the three methods:
    """
    )

    future_rets = expected_returns.mean_historical_return(future_df)
    mean_abs_errors = []

    for method in return_methods:
        mu = expected_returns.return_model(past_df, method=method)
        mean_abs_errors.append(np.sum(np.abs(mu - future_rets)) / len(mu))

    xrange = range(len(mean_abs_errors))
    fig, _ = plt.subplots()
    plt.barh(xrange, mean_abs_errors)
    plt.yticks(xrange, return_methods)
    st.pyplot(fig)

    st.markdown(
        """
    **Note: the absolute deviations are quite high!
    A deviation of 25%, means that if the expected returns are 10%, then you 
    can be gaining up to 35% or losing 15%.**
    """
    )

    fig, axs = plt.subplots(1, len(return_methods), sharey=True)
    for i, method in enumerate(return_methods):
        mu = expected_returns.return_model(past_df, method=method)
        axs[i].set_title(method)
        mu.plot.barh(ax=axs[i])
    st.pyplot(fig)

    st.markdown(
        """
    Just for reference, the real returns for the window we left out are the following:
    """
    )

    fig, ax = plt.subplots()
    ax.set_title("Real returns")
    real_mu = (future_df.iloc[-1] - past_df.iloc[-1]) / past_df.iloc[-1]
    real_mu.plot.barh(ax=ax)
    st.pyplot(fig)

    st.write(f"**Average return: {real_mu.mean()*100:.1f}%**")

    st.markdown(
        """
    **Note: It is hard to predict expected returns!**

    # Let's Optimize!
    """
    )

    lst = [
        ("Minimize volatility", models.min_volatility),
        ("Maximize return for a target risk", models.efficient_risk),
        ("Minimizing volatility for a given target return", models.efficient_return),
        ("Maximize the Sharpe Ratio", models.max_sharpe),
    ]
    model = st.selectbox("Pick the model 👇", [m[0] for m in lst], key="model")

    for label, impl in lst:
        if label == model and impl:
            impl(past_df, real_mu)
            break

    st.markdown(
        """
    # References

    - amplpy: https://amplpy.readthedocs.io
    - amplpyfinance: https://amplpy.readthedocs.io
    - PyPortfolioOpt: https://pyportfolioopt.readthedocs.io
    """
    )

    # Sidebar
    st.sidebar.header("About")
    st.sidebar.markdown(INFO_HEADER)

    st.sidebar.header("Resources")
    st.sidebar.markdown(INFO_FOOTER)
