#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
表达式括号简化程序测试脚本
测试简化版栈实现的括号简化功能
"""

from test import remove_extra_parentheses
import sys

def test_simplification(expression, expected):
    """
    测试单个表达式的括号简化功能
    
    Args:
        expression: 输入表达式
        expected: 期望结果
    
    Returns:
        测试是否通过
    """
    # 递归简化，直到没有可移除的括号
    simplified = expression
    while True:
        new_simplified = remove_extra_parentheses(simplified)
        if new_simplified == simplified:
            break
        simplified = new_simplified
    
    result = simplified == expected
    print(f"表达式: {expression}")
    print(f"简化结果: {simplified}")
    print(f"期望结果: {expected}")
    print(f"测试{'通过' if result else '失败'}!")
    print("-" * 50)
    return result

def run_all_tests():
    """
    运行所有测试用例
    """
    test_cases = [
        # 基础测试用例
        ("(1+2)", "1+2"),
        ("((1+2))", "1+2"),
        ("(1)+(2)", "1+2"),
        ("(1+2)*3", "1+2*3"),
        ("1*(2+3)", "1*(2+3)"),  # 括号需要保留
        ("(1*2)+(3*4)", "1*2+3*4"),
        ("1+(2*3)", "1+2*3"),  # 括号可以移除
        
        # 复杂运算符优先级测试
        ("(a+b)*c", "(a+b)*c"),  # 括号需要保留
        ("a+(b*c)", "a+b*c"),    # 括号可以移除
        ("(a*b)+c", "a*b+c"),    # 括号可以移除
        ("a*(b+c*d)", "a*(b+c*d)"),  # 括号需要保留
        ("(a*b)^c", "(a*b)^c"),      # 幂运算需要保留括号
        ("a^(b*c)", "a^(b*c)"),      # 幂运算需要保留括号
        
        # 负号处理测试
        ("a-((b+c))", "a-(b+c)"),    # 括号需要保留
        ("-(1+2)", "-(1+2)"),        # 括号需要保留
        ("-1*2", "-1*2"),            # 无需括号
        
        # 多嵌套括号测试
        (((((((((1+2))))))))), "1+2"),
        ("((a+b)*(c-d))", "(a+b)*(c-d)"),
        ("((a+b)+c)+d", "a+b+c+d"),
        ("a+(b+(c+d))", "a+b+c+d"),  # 左结合性
        ("a^(b^(c^d))", "a^(b^(c^d))"),  # 右结合性，括号需要保留
        
        # 特殊情况测试
        ("2^(1+2)", "2^(1+2)"),      # 幂运算需要保留括号
        ("(a+b)+(c+d)", "a+b+c+d"),
        ("(a*b)*(c*d)", "a*b*c*d"),
        ("(a+b)-(c-d)", "(a+b)-(c-d)"),
        ("(a/b)*(c/d)", "a/b*c/d"),
    ]
    
    passed = 0
    total = len(test_cases)
    
    print(f"开始测试，共 {total} 个测试用例")
    print("=" * 50)
    
    for expression, expected in test_cases:
        if test_simplification(expression, expected):
            passed += 1
    
    print(f"测试结果: {passed}/{total} 通过")
    print(f"通过率: {passed/total*100:.2f}%")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)