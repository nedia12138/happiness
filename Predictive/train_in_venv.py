"""
统一环境训练脚本
确保在 venv 环境中训练，避免版本不兼容问题
"""

import sys
import os

# 检查是否在 venv 环境中
def check_venv():
    """检查是否在虚拟环境中"""
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    return in_venv

def check_sklearn_version():
    """检查 scikit-learn 版本"""
    try:
        import sklearn
        return sklearn.__version__
    except ImportError:
        return None

def main():
    print("=" * 60)
    print("环境检查")
    print("=" * 60)
    
    # 检查虚拟环境
    if check_venv():
        print("✓ 运行在虚拟环境中")
    else:
        print("⚠️  警告: 未在虚拟环境中运行")
        print("建议: 先激活 venv 环境")
        print("  .\\venv\\Scripts\\Activate.ps1")
        response = input("\n是否继续？(y/n): ")
        if response.lower() != 'y':
            print("已取消")
            return
    
    # 检查 scikit-learn 版本
    sklearn_version = check_sklearn_version()
    if sklearn_version:
        print(f"✓ scikit-learn 版本: {sklearn_version}")
    else:
        print("✗ 未安装 scikit-learn")
        return
    
    print(f"✓ Python 路径: {sys.executable}")
    print(f"✓ Python 版本: {sys.version}")
    
    print("\n" + "=" * 60)
    print("开始训练模型...")
    print("=" * 60 + "\n")
    
    # 导入并运行训练脚本
    from simple_improved_training import SimpleImprovedModel
    
    try:
        model = SimpleImprovedModel()
        model.run()
        
        print("\n" + "=" * 60)
        print("✓ 训练完成！")
        print("=" * 60)
        print("\n提示: 请使用相同的环境启动应用")
        print(f"  {sys.executable} app.py")
        
    except Exception as e:
        print(f"\n✗ 训练失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

