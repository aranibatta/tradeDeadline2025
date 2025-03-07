import networkx as nx
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Define NBA team colors and name mappings
TEAM_COLORS = {
    'Hawks': '#E03A3E', 'Celtics': '#007A33', 'Nets': '#000000', 'Hornets': '#1D1160',
    'Bulls': '#CE1141', 'Cavaliers': '#860038', 'Mavericks': '#00538C', 'Nuggets': '#0E2240',
    'Pistons': '#C8102E', 'Warriors': '#1D428A', 'Rockets': '#CE1141', 'Pacers': '#002D62',
    'Clippers': '#C8102E', 'Lakers': '#552583', 'Grizzlies': '#5D76A9', 'Heat': '#98002E',
    'Bucks': '#00471B', 'Timberwolves': '#0C2340', 'Pelicans': '#0C2340', 'Knicks': '#006BB6',
    'Thunder': '#007AC1', 'Magic': '#0077C0', '76ers': '#006BB6', 'Suns': '#1D1160',
    'Trail Blazers': '#E03A3E', 'Kings': '#5A2D81', 'Spurs': '#C4CED4', 'Raptors': '#CE1141',
    'Jazz': '#002B5C', 'Wizards': '#002B5C'
}

def clean_team_name(team_name):
    """Clean team name to match the format in TEAM_COLORS dictionary."""
    # Remove any trailing/leading whitespace
    team = team_name.strip()
    # Extract team name from before the colon
    if ':' in team:
        team = team.split(':', 1)[0].strip()
    return team

def create_trade_network(trades_file, player_stats_file):
    """
    Create and visualize a network of NBA trades.
    
    Parameters:
    -----------
    trades_file : str
        Path to the CSV file containing trade information
    player_stats_file : str
        Path to the CSV file containing player statistics
    
    Returns:
    --------
    plotly.graph_objects.Figure
        The interactive network visualization
    dict
        Dictionary containing team PRA changes
    """
    # Read data
    trades = pd.read_csv(trades_file)
    player_stats = pd.read_csv(player_stats_file)
    player_stats_dict = player_stats.set_index('NAME')['P+R+A'].to_dict()

    # Initialize graph and tracking dict
    G = nx.Graph()
    team_pra_changes = {}

    # Process trades
    for _, row in trades.iterrows():
        trade_teams = []
        trade_details = {}
        trade_pra = {}
        
        for i in range(1, 6):
            team_col = f'Team{i}'
            if pd.notna(row[team_col]) and ':' in row[team_col]:
                team, players = row[team_col].split(':', 1)
                team = clean_team_name(team)
                players_list = [p.strip() for p in players.strip().split(';')]
                
                total_pra = sum(player_stats_dict.get(player, 0) for player in players_list)
                
                trade_teams.append(team)
                trade_details[team] = players_list
                trade_pra[team] = total_pra
                
                if team not in team_pra_changes:
                    team_pra_changes[team] = 0
        
        for i, team1 in enumerate(trade_teams):
            for team2 in trade_teams[i+1:]:
                G.add_edge(team1, team2, 
                           team1_players=trade_details[team1],
                           team2_players=trade_details[team2],
                           team1_pra=trade_pra[team1],
                           team2_pra=trade_pra[team2],
                           date=row['Date'])
                
                team_pra_changes[team1] += trade_pra[team2] - trade_pra[team1]
                team_pra_changes[team2] += trade_pra[team1] - trade_pra[team2]

    # Create layout
    pos = nx.spring_layout(G, dim=3, k=0.5, iterations=50)

    # Create edges
    edge_x, edge_y, edge_z = [], [], []
    for edge in G.edges():
        x0, y0, z0 = pos[edge[0]]
        x1, y1, z1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_z.extend([z0, z1, None])

    edge_trace = go.Scatter3d(x=edge_x, y=edge_y, z=edge_z, mode='lines',
                              line=dict(color='#888', width=1), hoverinfo='none')

    # Create nodes
    node_x, node_y, node_z = [], [], []
    node_colors = []
    for node in G.nodes():
        x, y, z = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_z.append(z)
        node_colors.append(TEAM_COLORS.get(node, '#888888'))

    node_text = [f"{team}<br>Net P+R+A Change: {team_pra_changes[team]:.2f}" 
                 for team in G.nodes()]

    node_trace = go.Scatter3d(x=node_x, y=node_y, z=node_z, mode='markers+text',
                              marker=dict(size=10, color=node_colors, line_width=2),
                              text=list(G.nodes()), textposition="top center",
                              hoverinfo='text', hovertext=node_text,
                              hoverlabel=dict(bgcolor='white', font_size=12))

    # Create figure
    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(title='NBA Trade Deadline 2025 - Team P+R+A Changes',
                      showlegend=False, hovermode='closest',
                      scene=dict(xaxis_visible=False, yaxis_visible=False, 
                                 zaxis_visible=False))
    
    return fig, team_pra_changes
