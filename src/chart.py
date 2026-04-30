import os
import platform
import logging
from datetime import date, timedelta

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import mplfinance as mpf
import pykrx.stock as krx

_KOREAN_FONT = "Malgun Gothic" if platform.system() == "Windows" else "NanumGothic"

logger = logging.getLogger(__name__)

CHARTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)

_STYLE = mpf.make_mpf_style(
    marketcolors=mpf.make_marketcolors(up="red", down="blue", volume="inherit"),
    gridstyle="--",
    gridcolor="#e0e0e0",
    rc={"font.family": _KOREAN_FONT, "axes.unicode_minus": False},
)

_3M_MAVS   = [5, 10, 20]
_1Y_MAVS   = [60, 120, 224, 448]
_3M_COLORS = ["royalblue", "darkorange", "green"]
_1Y_COLORS = ["royalblue", "darkorange", "green", "crimson"]


def _fetch_ohlcv(code: str, start: str, end: str) -> pd.DataFrame:
    df = krx.get_market_ohlcv_by_date(start, end, code)
    df = df.rename(columns={
        "시가": "Open", "고가": "High", "저가": "Low",
        "종가": "Close", "거래량": "Volume",
    })
    df.index.name = "Date"
    return df[["Open", "High", "Low", "Close", "Volume"]].dropna()


def _build_addplots(df_display: pd.DataFrame, df_full: pd.DataFrame,
                    mavs: list[int], colors: list[str]) -> list:
    """전체 df_full 기준으로 이평선 계산 후 표시 구간만 슬라이스."""
    n = len(df_display)
    plots = []
    for period, color in zip(mavs, colors):
        values = df_full["Close"].rolling(period).mean().values[-n:]
        ma = pd.Series(values, index=df_display.index)
        plots.append(mpf.make_addplot(ma, color=color, width=1.2))
    return plots


def _add_ma_legend(ax, mavs: list[int], colors: list[str]) -> None:
    handles = [
        mlines.Line2D([], [], color=c, linewidth=1.2, label=f"MA{p}")
        for p, c in zip(mavs, colors)
    ]
    ax.legend(handles=handles, loc="upper left", fontsize=8)


def _plot_and_save(df_display: pd.DataFrame, df_full: pd.DataFrame,
                   name: str, suffix: str,
                   mavs: list[int], colors: list[str], path: str) -> None:
    apds = _build_addplots(df_display, df_full, mavs, colors)
    fig, axes = mpf.plot(
        df_display,
        type="candle",
        volume=True,
        style=_STYLE,
        title=f"{name} {suffix}",
        addplot=apds,
        returnfig=True,
    )
    # 가격 Y축
    axes[0].set_ylabel("원")
    # 거래량 Y축 (mplfinance는 twin axes 구조로 volume이 axes[2]에 위치)
    vol_ax = axes[2] if len(axes) > 2 else axes[1]
    vol_ax.set_ylabel("억원")
    _add_ma_legend(axes[0], mavs, colors)
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def generate_charts(code: str, name: str, today: date) -> tuple[str, str]:
    end = today.strftime("%Y%m%d")
    start_2y = (today - timedelta(days=730)).strftime("%Y%m%d")

    df_full = _fetch_ohlcv(code, start_2y, end)
    if df_full.empty:
        raise ValueError(f"데이터 없음: {code}")

    path_3m = os.path.join(CHARTS_DIR, f"{code}_3M.png")
    path_1y = os.path.join(CHARTS_DIR, f"{code}_1Y.png")

    _plot_and_save(df_full.iloc[-63:],  df_full, name, "3M", _3M_MAVS, _3M_COLORS, path_3m)
    _plot_and_save(df_full.iloc[-250:], df_full, name, "1Y", _1Y_MAVS, _1Y_COLORS, path_1y)

    logger.info(f"차트 생성 완료: {code}")
    return path_3m, path_1y
