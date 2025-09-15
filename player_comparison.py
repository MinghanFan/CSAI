# player_comparison.py
"""Player similarity and comparison analysis."""

import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from data_structures import PlayerFingerprint
import config

class PlayerComparison:
    """Handles player similarity analysis and comparisons."""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=config.PCA_COMPONENTS)
    
    def compare_players(self, player_fingerprints: Dict[str, PlayerFingerprint]) -> Optional[Dict]:
        """Compare multiple players and return similarity analysis."""
        if len(player_fingerprints) < 2:
            return None
            
        feature_matrix = self._fingerprints_to_vectors(player_fingerprints)
        
        # Normalize features to prevent scale issues
        feature_matrix_scaled = self.scaler.fit_transform(feature_matrix)
        
        print(f"    Feature matrix shape: {feature_matrix_scaled.shape}")
        print(f"    Feature ranges after scaling: min={feature_matrix_scaled.min():.3f}, "
              f"max={feature_matrix_scaled.max():.3f}")
        
        similarity_matrix = cosine_similarity(feature_matrix_scaled)
        
        # PCA for visualization
        player_2d = self.pca.fit_transform(feature_matrix_scaled)
        
        return {
            'similarity_matrix': similarity_matrix,
            'visualization_coords': player_2d,
            'feature_matrix': feature_matrix_scaled,
            'original_features': feature_matrix,
            'player_names': list(player_fingerprints.keys())
        }
    
    def _fingerprints_to_vectors(self, player_fingerprints: Dict[str, PlayerFingerprint]) -> np.ndarray:
        """Convert player fingerprints to numerical feature vectors."""
        # Get all possible features from all players
        all_features = set()
        for fingerprint in player_fingerprints.values():
            if fingerprint:
                feature_dict = fingerprint.to_feature_vector()
                all_features.update(feature_dict.keys())
        
        all_features = sorted(list(all_features))
        print(f"    Using {len(all_features)} features for comparison")
        
        # Filter out non-numeric features and very large values
        numeric_features = []
        for feature in all_features:
            # Skip text features
            if any(text_indicator in feature.lower() for text_indicator in ['weapon', 'primary']):
                continue
            numeric_features.append(feature)
        
        print(f"    Using {len(numeric_features)} numeric features")
        
        # Convert fingerprints to feature vectors
        feature_vectors = []
        for player, fingerprint in player_fingerprints.items():
            vector = []
            feature_dict = fingerprint.to_feature_vector() if fingerprint else {}
            
            for feature in numeric_features:
                value = feature_dict.get(feature, 0)
                if isinstance(value, (int, float)) and not (isinstance(value, float) and np.isnan(value)):
                    # Cap very large values to prevent them from dominating similarity
                    if abs(value) > 1e6:
                        value = np.sign(value) * 1e6
                    vector.append(value)
                else:
                    vector.append(0)
            feature_vectors.append(vector)
        
        feature_matrix = np.array(feature_vectors)
        
        # Debug: show feature statistics
        print(f"    Feature matrix stats:")
        print(f"      Mean: {np.mean(feature_matrix, axis=0)[:5]}...")  # Show first 5
        print(f"      Std: {np.std(feature_matrix, axis=0)[:5]}...")   # Show first 5
        
        return feature_matrix
    
    def find_most_similar_players(self, target_player: str, all_players: Dict[str, PlayerFingerprint],
                                top_k: int = config.TOP_SIMILAR_PLAYERS) -> List[Dict]:
        """Find the most similar players to a target player."""
        comparison = self.compare_players(all_players)
        if not comparison or target_player not in all_players:
            return []
        
        player_names = comparison['player_names']
        target_idx = player_names.index(target_player)
        similarities = comparison['similarity_matrix'][target_idx]
        
        # Get indices sorted by similarity (excluding the target player)
        similar_indices = np.argsort(similarities)[::-1][1:top_k+1]
        
        similar_players = [
            {
                'player': player_names[idx],
                'similarity': float(similarities[idx])
            }
            for idx in similar_indices
        ]
        
        return similar_players