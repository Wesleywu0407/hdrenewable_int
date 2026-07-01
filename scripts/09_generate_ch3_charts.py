import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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


def fig1_state_mismatch():
    """Bar chart: State-by-State DC Count vs Firming Capacity."""
    df = pd.read_csv('data/processed_ch3/ch3_state_infrastructure.csv')
    df = df.sort_values('dc_count', ascending=False)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Bar(
        name='Data Centres (Count)',
        x=df['state'],
        y=df['dc_count'],
        marker_color='rgba(255,255,255,0.2)',
        hovertemplate='<b>%{x}</b><br>Data Centres: %{y}<extra></extra>',
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        name='BESS Capacity (GW)',
        x=df['state'],
        y=df['bess_gw'],
        mode='lines+markers',
        line=dict(color=ACCENT, width=3),
        marker=dict(size=8, color=ACCENT),
        hovertemplate='<b>%{x}</b><br>BESS: %{y:.1f} GW<extra></extra>',
    ), secondary_y=True)

    fig.add_trace(go.Scatter(
        name='Solar Capacity (GW)',
        x=df['state'],
        y=df['solar_gw'],
        mode='lines+markers',
        line=dict(color='#FAC775', width=3),
        marker=dict(size=8, color='#FAC775'),
        hovertemplate='<b>%{x}</b><br>Solar: %{y:.1f} GW<extra></extra>',
    ), secondary_y=True)

    fig.update_layout(
        xaxis_title='State',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
    )
    fig.update_yaxes(title_text="Data Centre Count", secondary_y=False)
    fig.update_yaxes(title_text="Capacity (GW)", secondary_y=True, showgrid=False)

    return apply_dark_theme(fig, height=480)


def fig2_hourly_profile():
    """Hourly Average Spot Price and Negative Events."""
    df = pd.read_csv('data/processed_ch3/ch3_hourly_profile.csv')

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Bar(
        name='Negative Price Events',
        x=df['hour'],
        y=df['negative_events'],
        marker_color='rgba(232,87,89,0.3)',
        hovertemplate='<b>Hour %{x}</b><br>Negative Events: %{y}<extra></extra>',
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        name='Average Spot Price ($/MWh)',
        x=df['hour'],
        y=df['price'],
        mode='lines',
        line=dict(color=ACCENT, width=3),
        hovertemplate='<b>Hour %{x}</b><br>Avg Price: $%{y:.2f}<extra></extra>',
    ), secondary_y=True)

    fig.update_layout(
        xaxis_title='Hour of Day',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
    )
    fig.update_xaxes(tickmode='linear', dtick=2)
    fig.update_yaxes(title_text="Negative Price Events", secondary_y=False)
    fig.update_yaxes(title_text="Avg Spot Price ($/MWh)", secondary_y=True, showgrid=False)

    return apply_dark_theme(fig, height=500)


def fig3_duck_curve():
    """Solar Irradiance vs Demand causing the Duck Curve."""
    df = pd.read_csv('data/processed_ch3/ch3_hourly_profile.csv')

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Scatter(
        name='Solar Irradiance (W/m²)',
        x=df['hour'],
        y=df['direct_radiation'],
        fill='tozeroy',
        fillcolor='rgba(250,199,117,0.1)',
        line=dict(color='#FAC775', width=2),
        mode='lines',
        hovertemplate='<b>Hour %{x}</b><br>Irradiance: %{y:.1f} W/m²<extra></extra>',
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        name='Average Demand (MW)',
        x=df['hour'],
        y=df['demand'],
        mode='lines',
        line=dict(color='rgba(255,255,255,0.8)', width=2, dash='dash'),
        hovertemplate='<b>Hour %{x}</b><br>Demand: %{y:.0f} MW<extra></extra>',
    ), secondary_y=True)

    fig.update_layout(
        xaxis_title='Hour of Day',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
    )
    fig.update_xaxes(tickmode='linear', dtick=2)
    fig.update_yaxes(title_text="Solar Irradiance (W/m²)", secondary_y=False)
    fig.update_yaxes(title_text="Average Demand (MW)", secondary_y=True, showgrid=False)

    return apply_dark_theme(fig, height=480)


def fig4_firming_value():
    """Cumulative Cost Comparison: Grid vs Firmed with BESS."""
    df = pd.read_csv('data/processed_ch3/ch3_firming_case.csv')
    df = df.sort_values('date')
    
    df['cum_grid_cost'] = df['daily_grid_cost'].cumsum()
    df['cum_firmed_cost'] = df['net_firmed_cost'].cumsum()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        name='Unfirmed Grid Cost ($)',
        x=df['date'],
        y=df['cum_grid_cost'],
        mode='lines',
        line=dict(color='rgba(255,255,255,0.3)', width=2, dash='dot'),
        hovertemplate='<b>%{x}</b><br>Grid Cost: $%{y:,.0f}<extra></extra>',
    ))

    fig.add_trace(go.Scatter(
        name='Firmed Cost (with BESS) ($)',
        x=df['date'],
        y=df['cum_firmed_cost'],
        mode='lines',
        fill='tonexty',
        fillcolor='rgba(0,217,163,0.1)',
        line=dict(color=ACCENT, width=3),
        hovertemplate='<b>%{x}</b><br>Firmed Cost: $%{y:,.0f}<extra></extra>',
    ))

    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Cumulative Power Cost ($)',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
    )

    return apply_dark_theme(fig, height=480)


if __name__ == '__main__':
    out = Path('outputs/figures')
    out.mkdir(parents=True, exist_ok=True)

    print('Generating Empirical Chapter 3 figures...')

    figures = [
        ('ch3_fig1_state_mismatch.html', fig1_state_mismatch),
        ('ch3_fig2_hourly_profile.html', fig2_hourly_profile),
        ('ch3_fig3_duck_curve.html', fig3_duck_curve),
        ('ch3_fig4_firming_value.html', fig4_firming_value),
    ]

    for filename, func in figures:
        print(f'  → {filename}')
        fig = func()
        fig.write_html(
            out / filename,
            config={'displayModeBar': False},
            include_plotlyjs='cdn',
        )

    print('Done!')
