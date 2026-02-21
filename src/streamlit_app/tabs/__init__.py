"""
Application tabs module.
"""
from .tab_funds import render_tab_funds
from .tab_portfolios import render_tab_portfolios

__all__ = [
    'render_tab_funds',
    'render_tab_portfolios',
]