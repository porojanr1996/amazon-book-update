#!/usr/bin/env python3
"""
Script pentru procesarea tuturor screenshot-urilor Amazon și extragerea BSR-ului
"""
import sys
import os
from pathlib import Path
import argparse
import subprocess

def find_screenshots(screenshot_dir: str) -> list:
    """Find all Amazon BSR screenshots in directory"""
    dir_path = Path(screenshot_dir)
    if not dir_path.exists():
        print(f"❌ Directorul nu există: {screenshot_dir}")
        return []
    
    screenshots = list(dir_path.glob('amazon_bsr_*.png'))
    screenshots.sort(key=lambda p: p.stat().st_mtime, reverse=True)  # Most recent first
    return screenshots


def process_screenshot(screenshot_path: Path) -> dict:
    """Process a single screenshot and extract BSR"""
    print(f"\n{'='*60}")
    print(f"📸 Procesare: {screenshot_path.name}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            [sys.executable, 'extract_bsr_from_screenshot.py', str(screenshot_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # Extract BSR from output
            output_lines = result.stdout.split('\n')
            bsr = None
            for line in output_lines:
                if 'BSR EXTRAS:' in line or 'BSR extracted' in line:
                    # Try to extract number
                    import re
                    match = re.search(r'#?(\d{1,3}(?:,\d{3})*)', line)
                    if match:
                        bsr_str = match.group(1).replace(',', '')
                        bsr = int(bsr_str)
                        break
            
            return {
                'success': True,
                'bsr': bsr,
                'screenshot': screenshot_path,
                'output': result.stdout
            }
        else:
            return {
                'success': False,
                'bsr': None,
                'screenshot': screenshot_path,
                'error': result.stderr or result.stdout
            }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'bsr': None,
            'screenshot': screenshot_path,
            'error': 'Timeout processing screenshot'
        }
    except Exception as e:
        return {
            'success': False,
            'bsr': None,
            'screenshot': screenshot_path,
            'error': str(e)
        }


def main():
    parser = argparse.ArgumentParser(description='Process all Amazon BSR screenshots and extract BSR values')
    parser.add_argument('--dir', default='/tmp/amazon_screenshots', help='Screenshot directory')
    parser.add_argument('--limit', type=int, help='Limit number of screenshots to process')
    parser.add_argument('--show-all', action='store_true', help='Show all results, including failures')
    
    args = parser.parse_args()
    
    print("="*60)
    print("🔍 PROCESARE SCREENSHOT-URI AMAZON PENTRU BSR")
    print("="*60)
    print()
    
    screenshots = find_screenshots(args.dir)
    
    if not screenshots:
        print(f"❌ Nu s-au găsit screenshot-uri în: {args.dir}")
        sys.exit(1)
    
    print(f"📸 Găsite {len(screenshots)} screenshot-uri")
    if args.limit:
        screenshots = screenshots[:args.limit]
        print(f"   Limitat la {len(screenshots)} screenshot-uri")
    print()
    
    results = []
    for i, screenshot in enumerate(screenshots, 1):
        print(f"\n[{i}/{len(screenshots)}] Procesare: {screenshot.name}")
        result = process_screenshot(screenshot)
        results.append(result)
        
        if result['success'] and result['bsr']:
            print(f"✅ BSR extras: #{result['bsr']:,}")
        elif args.show_all:
            print(f"❌ Eșec: {result.get('error', 'Unknown error')}")
    
    # Summary
    print("\n" + "="*60)
    print("📊 REZUMAT")
    print("="*60)
    
    successful = [r for r in results if r['success'] and r['bsr']]
    failed = [r for r in results if not r['success'] or not r['bsr']]
    
    print(f"✅ Succes: {len(successful)}/{len(results)}")
    print(f"❌ Eșec: {len(failed)}/{len(results)}")
    
    if successful:
        print("\n📋 BSR-uri extrase:")
        for r in successful:
            print(f"   {r['screenshot'].name}: #{r['bsr']:,}")
    
    if failed and args.show_all:
        print("\n❌ Eșecuri:")
        for r in failed:
            print(f"   {r['screenshot'].name}: {r.get('error', 'BSR not found')}")
    
    print()
    
    if successful:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

