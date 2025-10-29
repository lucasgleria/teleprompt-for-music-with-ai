import unittest
from unittest.mock import patch
import tkinter as tk
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

with patch('pygame.mixer'):
    from src.music_player import MusicPlayer

class TestMusicPlayer(unittest.TestCase):
    @patch('pygame.mixer')
    def test_instantiation(self, mock_mixer):
        root = tk.Tk()
        player = MusicPlayer(root)
        self.assertIsInstance(player, MusicPlayer)
        root.destroy()

if __name__ == "__main__":
    unittest.main()
