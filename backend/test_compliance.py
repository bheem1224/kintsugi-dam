import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import sys
import os

# Adjust paths to import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "VScode-Projects", "Kintsugi-Enterprise-Dev", "kintsugi-dam", "backend")))

from app.modules.remediators.snapshots.heuristic import SnapshotHeuristicResolver
from app.modules.scanners.daemon import run_scanner_daemon
from app.core.models import SystemSettings

class TestCompliance(unittest.IsolatedAsyncioTestCase):
    
    @patch("os.scandir")
    @patch("pathlib.Path.stat")
    def test_heuristic_resolver_regex_caching(self, mock_stat, mock_scandir):
        # Setup mock method for Path.exists
        def exists_method(self_path):
            p_str = str(self_path).replace('\\', '/')
            # We want to match /snapshots/dataset1/snap_20260520/dataset1/subdir/file.jpg
            # but NOT with the "/media" prefix included.
            if "media/dataset1" in p_str:
                return False
            if p_str.endswith("dataset1/subdir/file.jpg"):
                return True
            if p_str == "/snapshots/dataset1": # mount path check
                return True
            return False

        # Mock Path.stat to return a dummy mtime
        mock_stat_val = MagicMock()
        mock_stat_val.st_mtime = 1000.0
        mock_stat.return_value = mock_stat_val
        
        # Mocking os.scandir to simulate directory entries during discovery
        mock_snap_dir = MagicMock()
        mock_snap_dir.is_dir.return_value = True
        mock_snap_dir.path = "/snapshots/dataset1/snap_20260520"
        
        mock_scandir.return_value = [mock_snap_dir]
        
        resolver = SnapshotHeuristicResolver()
        
        # First call: target file "/media/dataset1/subdir/file.jpg"
        target_path = Path("/media/dataset1/subdir/file.jpg")
        mount_path = Path("/snapshots/dataset1")
        
        # Run resolution with Path.exists patched as a function
        with patch("pathlib.Path.exists", exists_method):
            versions = resolver.get_snapshot_versions(mount_path, target_path)
            
            # Verify it discovered the structure and cached the pattern
            self.assertIsNotNone(resolver._cached_pattern)
            regex, base = resolver._cached_pattern
            self.assertEqual(base, mount_path)
            self.assertTrue(regex.match("/media/dataset1/subdir/file.jpg"))
            
            # Now reset mock_scandir to verify it's NOT called again during subsequent path resolution
            mock_scandir.reset_mock()
            
            # Second call to a different file in another nested directory (e.g. "/media/dataset1/another_dir/another_file.png")
            another_target = Path("/media/dataset1/another_dir/another_file.png")
            
            with patch.object(resolver, "_discover_structure") as mock_discover:
                versions2 = resolver.get_snapshot_versions(mount_path, another_target)
                mock_discover.assert_not_called() # Crucial check: discovery is bypassed!

    @patch("app.modules.scanners.daemon.SessionLocal")
    @patch("app.core.scanner.FileScanner.process_file", new_callable=AsyncMock)
    async def test_license_tier_enforcement(self, mock_process_file, mock_session_maker):
        # 1. Setup mock session and settings
        mock_session = AsyncMock()
        mock_session_maker.return_value.__aenter__.return_value = mock_session
        
        # Case A: Free Tier
        mock_res_tier = MagicMock()
        mock_res_tier.scalars.return_value.first.return_value = "free"
        
        mock_res_workers = MagicMock()
        mock_res_workers.scalars.return_value.first.return_value = "8"
        
        mock_session.execute.side_effect = [mock_res_tier, mock_res_workers]
        
        # Mock file paths generator
        async def mock_generator():
            yield "/media/file1.jpg"
            
        with patch("app.modules.scanners.daemon.logger") as mock_logger:
            await run_scanner_daemon(mock_generator())
            
            # Verify daemon logged starting with exactly 1 worker
            mock_logger.info.assert_any_call("Starting scanner daemon with 1 workers (Pro tier: False)")

        # Case B: Pro Tier
        mock_res_tier_pro = MagicMock()
        mock_res_tier_pro.scalars.return_value.first.return_value = "pro"
        
        mock_res_workers_pro = MagicMock()
        mock_res_workers_pro.scalars.return_value.first.return_value = "4"
        
        mock_session.execute.side_effect = [mock_res_tier_pro, mock_res_workers_pro]
        
        with patch("app.modules.scanners.daemon.logger") as mock_logger:
            await run_scanner_daemon(mock_generator())
            
            # Verify daemon logged starting with exactly 4 workers
            mock_logger.info.assert_any_call("Starting scanner daemon with 4 workers (Pro tier: True)")

if __name__ == "__main__":
    unittest.main()
