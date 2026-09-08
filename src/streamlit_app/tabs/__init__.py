"""
Application tabs module.
"""
from .tab_funds import render_tab_funds
from .tab_portfolios import render_tab_portfolios
from .tab_available_funds import render_tab_available_funds

__all__ = [
    'render_tab_funds',
    'render_tab_portfolios',
    'render_tab_available_funds',
]