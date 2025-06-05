#!/usr/bin/env python3
"""
SwarmDev File Cleanup and Duplicate Management Demo

This script demonstrates the enhanced file management capabilities that address
the common issue of AI agents creating duplicate files instead of modifying 
existing ones.

Features demonstrated:
1. File duplicate detection and analysis
2. Automatic cleanup of obsolete files
3. Preference for modification over creation
4. Smart file consolidation
"""

import os
import sys
import json
from pathlib import Path

# Add SwarmDev to path
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root / "src"))

from swarmdev.swarm_builder.agents.base_agent import BaseAgent
from swarmdev.utils.llm_provider import LLMProviderFactory

class FileDuplicateDemo:
    """Demonstration of SwarmDev's enhanced file management capabilities."""
    
    def __init__(self, project_dir: str):
        self.project_dir = project_dir
        
        # Initialize a basic agent for file management
        try:
            # Try to get LLM provider for enhanced features
            llm_provider = LLMProviderFactory.create_provider()
            self.agent = BaseAgent("demo", "demo", llm_provider=llm_provider)
        except Exception:
            print("Warning: No LLM provider available, some features will be limited")
            self.agent = BaseAgent("demo", "demo")
    
    def create_test_duplicates(self):
        """Create test duplicate files to demonstrate cleanup."""
        print("\n=== Creating Test Duplicate Files ===")
        
        test_files = {
            "agents/base_agent.py": '''"""Base agent implementation."""\n\nclass BaseAgent:\n    def __init__(self):\n        pass\n''',
            "agents/_base.py": '''"""Legacy base agent."""\n\nclass BaseAgent:\n    def __init__(self):\n        # Old implementation\n        pass\n''',
            "agents/base.py": '''"""Another base agent variant."""\n\nclass Agent:\n    pass\n''',
            "config/config.py": '''"""Configuration module."""\n\nCONFIG = {}\n''',
            "config/settings.py": '''"""Settings configuration."""\n\nSETTINGS = {}\n''',
            "main.py": '''"""Main application."""\n\nif __name__ == "__main__":\n    print("Hello World")\n''',
            "app.py": '''"""Application entry point."""\n\nif __name__ == "__main__":\n    print("App started")\n''',
        }
        
        os.makedirs(self.project_dir, exist_ok=True)
        
        for file_path, content in test_files.items():
            full_path = Path(self.project_dir) / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w') as f:
                f.write(content)
            
            print(f"Created: {file_path}")
        
        print(f"\nCreated {len(test_files)} test files with potential duplicates")
    
    def analyze_duplicates(self):
        """Demonstrate duplicate file analysis."""
        print("\n=== Analyzing File Duplicates ===")
        
        try:
            analysis = self.agent.analyze_file_duplicates(self.project_dir)
            
            print(f"Total files analyzed: {analysis.get('total_files', 0)}")
            print(f"Potential duplicates found: {analysis.get('potential_duplicates', 0)}")
            
            duplicate_groups = analysis.get("duplicate_groups", {})
            if duplicate_groups:
                print("\nDuplicate Groups Found:")
                for base_name, files in duplicate_groups.items():
                    if len(files) > 1:
                        print(f"  {base_name}: {', '.join(files)}")
            
            recommendations = analysis.get("recommendations", [])
            if recommendations:
                print("\nCleanup Recommendations:")
                for rec in recommendations:
                    print(f"  - {rec}")
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing duplicates: {e}")
            return {}
    
    def demonstrate_cleanup(self, analysis, dry_run=True):
        """Demonstrate file cleanup capabilities."""
        print(f"\n=== {'Simulating' if dry_run else 'Performing'} File Cleanup ===")
        
        if not analysis.get("duplicate_groups"):
            print("No duplicates found to clean up")
            return
        
        try:
            if dry_run:
                print("DRY RUN - No files will actually be deleted")
                
                duplicate_groups = analysis.get("duplicate_groups", {})
                for base_name, files in duplicate_groups.items():
                    if len(files) > 1:
                        main_file = self.agent._identify_main_file(files)
                        others = [f for f in files if f != main_file]
                        
                        print(f"\nGroup '{base_name}':")
                        print(f"  Would keep: {main_file}")
                        print(f"  Would remove: {', '.join(others)}")
            else:
                # Perform actual cleanup
                cleanup_results = self.agent.cleanup_duplicate_files(
                    self.project_dir, analysis, auto_confirm=True
                )
                
                print("Cleanup Results:")
                print(f"  Files removed: {len(cleanup_results.get('removed', []))}")
                print(f"  Files skipped: {len(cleanup_results.get('skipped', []))}")
                print(f"  Errors: {len(cleanup_results.get('errors', []))}")
                
                if cleanup_results.get("removed"):
                    print("  Removed files:")
                    for file in cleanup_results["removed"]:
                        print(f"    - {file}")
                
                return cleanup_results
                
        except Exception as e:
            print(f"Error during cleanup: {e}")
            return {}
    
    def demonstrate_consolidation(self):
        """Demonstrate file consolidation capabilities."""
        print("\n=== File Consolidation Demo ===")
        
        # Find files that could be consolidated
        try:
            base_files = []
            for root, dirs, files in os.walk(self.project_dir):
                for file in files:
                    if "base" in file.lower() and file.endswith('.py'):
                        rel_path = os.path.relpath(os.path.join(root, file), self.project_dir)
                        base_files.append(rel_path)
            
            if len(base_files) > 1:
                print(f"Found {len(base_files)} base-related files that could be consolidated:")
                for file in base_files:
                    print(f"  - {file}")
                
                # Demonstrate consolidation (dry run)
                print("\nConsolidation would:")
                print(f"  1. Choose best file as primary: {base_files[0]}")
                print(f"  2. Merge content from: {', '.join(base_files[1:])}")
                print(f"  3. Remove redundant files")
                print(f"  4. Update imports if needed")
            else:
                print("No files found for consolidation demonstration")
                
        except Exception as e:
            print(f"Error demonstrating consolidation: {e}")
    
    def show_enhanced_workflow_features(self):
        """Show how enhanced workflows prevent duplication."""
        print("\n=== Enhanced Workflow Features ===")
        
        print("SwarmDev's Enhanced Iteration Workflow now includes:")
        print("  ✓ Duplicate file detection during analysis phase")
        print("  ✓ Preference for modifying existing files over creating new ones")
        print("  ✓ Automatic cleanup of obsolete files after improvements")
        print("  ✓ Smart file consolidation recommendations")
        print("  ✓ Project structure awareness before making changes")
        
        print("\nWorkflow Parameters for File Management:")
        print("  - cleanup_duplicates: True (automatic duplicate detection)")
        print("  - prefer_modification_over_creation: True (modify vs create)")
        print("  - cleanup_obsolete_files: True (remove old files)")
        print("  - include_cleanup_plan: True (plan cleanup in advance)")
        
        print("\nThis prevents issues like:")
        print("  ❌ base_agent.py, _base.py, base.py (multiple similar files)")
        print("  ❌ Creating new files when existing ones could be enhanced")
        print("  ❌ Accumulating obsolete code over iterations")
        
    def cleanup_test_files(self):
        """Clean up the test files created for demonstration."""
        print("\n=== Cleaning Up Test Files ===")
        
        try:
            import shutil
            if os.path.exists(self.project_dir):
                shutil.rmtree(self.project_dir)
                print(f"Removed test directory: {self.project_dir}")
        except Exception as e:
            print(f"Error cleaning up: {e}")

def main():
    """Run the file cleanup demonstration."""
    print("SwarmDev File Cleanup and Duplicate Management Demo")
    print("=" * 50)
    
    # Use a test directory
    test_dir = "/tmp/swarmdev_file_demo"
    demo = FileDuplicateDemo(test_dir)
    
    try:
        # 1. Create test duplicates
        demo.create_test_duplicates()
        
        # 2. Analyze duplicates
        analysis = demo.analyze_duplicates()
        
        # 3. Demonstrate cleanup (dry run)
        demo.demonstrate_cleanup(analysis, dry_run=True)
        
        # 4. Show consolidation features
        demo.demonstrate_consolidation()
        
        # 5. Show enhanced workflow features
        demo.show_enhanced_workflow_features()
        
        # 6. Ask user if they want to see actual cleanup
        print("\n" + "=" * 50)
        response = input("Would you like to see actual cleanup in action? (y/N): ").lower()
        
        if response == 'y':
            demo.demonstrate_cleanup(analysis, dry_run=False)
            print("\nRe-analyzing after cleanup:")
            demo.analyze_duplicates()
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\nDemo failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up test files
        demo.cleanup_test_files()

if __name__ == "__main__":
    main() 