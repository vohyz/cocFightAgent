#!/usr/bin/env python3
# === run_demo.py ===

"""
CoC战斗系统快速启动脚本

使用方法:
    python run_demo.py
"""

import asyncio
import sys
import os
from pathlib import Path

src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

async def main():
    from src.coc_keeper_demo import main as demo_main
    await demo_main()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 再见！")
    # except Exception as e:
    #     print(f"❌ 运行出错: {e}")
    #     print("请检查环境配置和依赖安装") 