import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# -- Color Settings (Consistent with Dashboard) ------------------------------
BG = 'rgba(0,0,0,0)'
GRID = 'rgba(255,255,255,0.06)'
TEXT_PRIMARY = '#F5F5F0'
TEXT_SECONDARY = '#B8BDB9'
TEXT_MUTED = '#6B7570'
ACCENT = '#00D9A3'
FONT = 'Inter, system-ui, sans-serif'

def apply_dark_theme(fig, height=520):
    """Apply consistent dark theme to all figures."""
    fig.update_layout(
        plot_bgcolor=BG,
        paper_bgcolor=BG,
        font=dict(family=FONT, color=TEXT_SECONDARY, size=12),
        height=height,
        margin=dict(l=60, r=20, t=40, b=50),
        legend=dict(
            bgcolor='rgba(0,0,0,0)',
            bordercolor=GRID,
            borderwidth=0.5,
            font=dict(color=TEXT_SECONDARY, size=11),
        ),
        hoverlabel=dict(
            bgcolor='#111A16',
            bordercolor='rgba(255,255,255,0.12)',
            font=dict(color='#FFFFFF', family=FONT, size=12),
        ),
    )
    fig.update_xaxes(
        gridcolor=GRID,
        zerolinecolor='rgba(255,255,255,0.12)',
        tickfont=dict(color=TEXT_MUTED, size=11),
        title_font=dict(color=TEXT_SECONDARY, size=12),
        linecolor='rgba(255,255,255,0.12)',
    )
    fig.update_yaxes(
        gridcolor=GRID,
        zerolinecolor='rgba(255,255,255,0.12)',
        tickfont=dict(color=TEXT_MUTED, size=11),
        title_font=dict(color=TEXT_SECONDARY, size=12),
        linecolor='rgba(255,255,255,0.12)',
    )
    return fig


def fig1_international_comparison():
    """Bar chart: Australia vs international DC capacity."""
    df = pd.read_csv('data/processed_ch3/international_dc_capacity.csv')
    df = df.sort_values('capacity_gw', ascending=True)

    colors = [ACCENT if c == 'Australia' else 'rgba(255,255,255,0.15)'
              for c in df['country']]

    fig = go.Figure(go.Bar(
        x=df['capacity_gw'].tolist(),
        y=df['country'].tolist(),
        orientation='h',
        marker_color=colors,
        text=[f'{v:.1f} GW' for v in df['capacity_gw']],
        textposition='outside',
        textfont=dict(color=TEXT_SECONDARY, size=11),
        hovertemplate='<b>%{y}</b><br>Capacity: %{x:.1f} GW<br>Growth rate: %{customdata}%/yr<extra></extra>',
        customdata=df['growth_rate_pct'].tolist(),
    ))

    fig.update_layout(
        xaxis_title='Installed Capacity (GW)',
        showlegend=False,
    )

    # Annotate Australia dynamically
    au = df[df['country'] == 'Australia'].iloc[0]
    fig.add_annotation(
        x=au['capacity_gw'],
        y='Australia',
        text=f"Strong APAC Player<br>{au['growth_rate_pct']}%/yr",
        showarrow=True,
        arrowhead=2,
        arrowcolor=ACCENT,
        font=dict(color=ACCENT, size=10),
        bgcolor='rgba(0,0,0,0)',
        ax=40,
        ay=-30,
        yref='y',
    )

    return apply_dark_theme(fig, height=480)


def fig2_demand_forecast():
    """Demand forecast 2025-2050."""
    df = pd.read_csv('data/processed_ch3/dc_demand_forecast.csv')

    fig = go.Figure()

    scenarios = [
        ('step_change_twh', ACCENT, 3, 'Step Change (AEMO Baseline)'),
        ('progressive_change_twh', 'rgba(255,255,255,0.5)', 1.5, 'Progressive Change'),
        ('green_energy_exports_twh', '#FAC775', 1.5, 'Green Energy Exports'),
    ]

    for col, color, width, name in scenarios:
        fig.add_trace(go.Scatter(
            x=df['year'],
            y=df[col],
            name=name,
            line=dict(color=color, width=width),
            mode='lines',
            hovertemplate=f'<b>{name}</b><br>Year: %{{x}}<br>Demand: %{{y:.1f}} TWh<extra></extra>',
        ))

    # Vertical line at 2026 (now)
    fig.add_vline(
        x=2026,
        line_dash='dash',
        line_color='rgba(255,255,255,0.2)',
        annotation_text='Now',
        annotation_font_color=TEXT_MUTED,
    )

    # Annotation for 2030 removed to avoid hardcoded artificial spike logic


    fig.update_layout(
        xaxis_title='Year',
        yaxis_title='Energy Demand (TWh)',
        yaxis=dict(range=[0, 40]),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
    )

    return apply_dark_theme(fig, height=500)


def fig3_renewable_gap():
    """Area chart: Green energy supply vs DC demand gap."""
    df = pd.read_csv('data/processed_ch3/dc_demand_forecast.csv')
    df = df[df['year'] <= 2035].copy()

    # Estimate renewable supply available for DCs
    # Assume renewable supply grows but lags demand
    df['renewable_supply_twh'] = df['step_change_twh'] * 0.45
    df['gap_twh'] = df['step_change_twh'] - df['renewable_supply_twh']

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['year'],
        y=df['step_change_twh'],
        name='Total DC Demand',
        fill='tozeroy',
        fillcolor='rgba(255,255,255,0.06)',
        line=dict(color='rgba(255,255,255,0.3)', width=1),
        mode='lines',
    ))

    fig.add_trace(go.Scatter(
        x=df['year'],
        y=df['renewable_supply_twh'],
        name='Available Renewable Supply',
        fill='tozeroy',
        fillcolor=f'rgba(0,217,163,0.2)',
        line=dict(color=ACCENT, width=2),
        mode='lines',
    ))

    # Gap area (area between supply and demand)
    fig.add_trace(go.Scatter(
        x=df['year'],
        y=df['step_change_twh'], # Plot up to total demand to fill the gap correctly
        name='Green Energy Gap (HDRE Opportunity)',
        fill='tonexty', # Fills from the previous trace (Available Renewable Supply)
        fillcolor='rgba(232,87,89,0.2)',
        line=dict(color='rgba(0,0,0,0)', width=0), # Hide the line, just show fill
        mode='lines',
        showlegend=False,
    ))

    # Add a separate line for the gap value if needed, or just let the fill do the work
    # We will just label the gap dynamically
    gap_2032 = df.loc[df['year'] == 2032, 'step_change_twh'].values[0]
    supply_2032 = df.loc[df['year'] == 2032, 'renewable_supply_twh'].values[0]
    mid_y_2032 = (gap_2032 + supply_2032) / 2

    fig.add_annotation(
        x=2032, y=mid_y_2032,
        text='HDRE Opportunity<br>Zone',
        showarrow=False,
        font=dict(color='#E85759', size=11),
    )

    fig.update_layout(
        xaxis_title='Year',
        yaxis_title='Energy (TWh)',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
    )

    return apply_dark_theme(fig, height=480)


def fig4_state_breakdown():
    """Grouped bar: State DC pipeline vs renewable share."""
    df = pd.read_csv('data/processed_ch3/state_dc_vs_renewable.csv')

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Existing DC (MW)',
        x=df['state'],
        y=df['dc_capacity_mw'],
        marker_color='rgba(255,255,255,0.3)',
        hovertemplate='<b>%{x}</b><br>Existing: %{y:,} MW<extra></extra>',
    ))

    fig.add_trace(go.Bar(
        name='Planned Pipeline (MW)',
        x=df['state'],
        y=df['dc_planned_mw'],
        marker_color=ACCENT,
        hovertemplate='<b>%{x}</b><br>Planned: %{y:,} MW<extra></extra>',
    ))

    # Renewable share as line on secondary axis
    fig.add_trace(go.Scatter(
        name='Renewable Share 2025 (%)',
        x=df['state'],
        y=df['renewable_share_pct_2025'],
        yaxis='y2',
        mode='lines+markers',
        line=dict(color='#FAC775', width=2),
        marker=dict(size=8, color='#FAC775'),
        hovertemplate='<b>%{x}</b><br>Renewables: %{y}%<extra></extra>',
    ))

    fig.update_layout(
        barmode='stack',
        xaxis_title='NEM State',
        yaxis=dict(
            title=dict(
                text='Capacity (MW)',
                font=dict(color=TEXT_SECONDARY)
            )
        ),
        yaxis2=dict(
            title=dict(
                text='Renewable Share (%)',
                font=dict(color='#FAC775')
            ),
            tickfont=dict(color='#FAC775'),
            overlaying='y',
            side='right',
            range=[0, 120],
            showgrid=False,
        ),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
    )

    return apply_dark_theme(fig, height=480)


# -- Main: generate all figures ---------------------------------
if __name__ == '__main__':
    out = Path('outputs/figures')
    out.mkdir(parents=True, exist_ok=True)

    print('Generating Chapter 3 figures...')

    figures = [
        ('ch3_fig1_international_comparison.html', fig1_international_comparison),
        ('ch3_fig2_demand_forecast.html', fig2_demand_forecast),
        ('ch3_fig3_renewable_gap.html', fig3_renewable_gap),
        ('ch3_fig4_state_breakdown.html', fig4_state_breakdown),
    ]

    for filename, func in figures:
        print(f'  → {filename}')
        fig = func()
        fig.write_html(
            out / filename,
            config={'displayModeBar': False},
            include_plotlyjs='cdn',
        )

    print('Done! All 4 Chapter 3 figures saved to outputs/figures/')
    print()
    print('Files created:')
    for filename, _ in figures:
        print(f'  outputs/figures/{filename}')
