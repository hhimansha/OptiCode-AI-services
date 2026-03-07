"""
Unified AST Refactoring Module
Combines ALL AST refactoring patterns into one comprehensive function
Location: IT22606860-code-refactor-python/unified_refactor.py
"""

import ast
import astor
from typing import Dict, List, Optional
import time

# Import all AST refactoring modules
from ast_refactor import refactor_code_ast, analyze_code_structure, suggest_refactorings
from priority_refactorings import apply_priority_refactorings, get_priority_patterns
from advanced_ast_refactor import refactor_comprehensive, list_all_patterns
from code_analyzer import analyze_code
from best_practices import check_best_practices
from ethical_code_analyzer import analyze_ethical_code
from architecture_analyzer import analyze_architecture
from performance_optimizer import optimize_performance
from unified_risk_refactor import refactor_risk_and_performance
from security_ast_refactor import run_security_refactoring


def refactor_complete(code: str, options: Optional[Dict] = None) -> Dict:
    """
    🚀 UNIFIED COMPREHENSIVE REFACTORING
    
    Applies ALL AST refactoring patterns in the correct order:
    1. Basic AST refactoring (ast_refactor.py)
    2. Priority patterns (priority_refactorings.py) 
    3. Advanced comprehensive patterns (advanced_ast_refactor.py)
    4. Code analysis
    5. Architecture analysis
    6. Performance optimization
    
    Args:
        code: Python source code to refactor
        options: Optional configuration:
            - apply_basic: bool (default True)
            - apply_priority: bool (default True)
            - apply_advanced: bool (default True)
            - apply_performance: bool (default True)
            - categories: List[str] (optional filter for advanced refactoring)
    
    Returns:
        Comprehensive refactoring result with all patterns applied
    """
    
    if options is None:
        options = {
            'apply_basic': True,
            'apply_priority': True,
            'apply_advanced': True,
            'apply_performance': True,
            'categories': None
        }
    
    start_time = time.time()
    
    results = {
        'success': True,
        'original_code': code,
        'refactored_code': code,
        'stages': {},
        'all_changes': [],
        'all_suggestions': [],
        'analysis': {},
        'processing_time_ms': 0
    }
    
    current_code = code
    
    try:
        # ============================================
        # STAGE 1: BASIC AST REFACTORING
        # ============================================
        if options.get('apply_basic', True):
            print("[UNIFIED] Stage 1: Basic AST refactoring...")
            basic_result = refactor_code_ast(current_code)
            
            if basic_result.get('success'):
                current_code = basic_result.get('refactored_code', current_code)
                results['stages']['basic'] = {
                    'applied': True,
                    'changes': basic_result.get('changes', []),
                    'warnings': basic_result.get('warnings', [])
                }
                results['all_changes'].extend(basic_result.get('changes', []))
                results['all_suggestions'].extend(basic_result.get('suggestions', []))
                print(f"[UNIFIED]   ✅ Basic: {len(basic_result.get('changes', []))} changes")
            else:
                results['stages']['basic'] = {'applied': False, 'error': basic_result.get('error')}
                print(f"[UNIFIED]   ⚠️  Basic failed: {basic_result.get('error')}")
        
        # ============================================
        # STAGE 2: PRIORITY REFACTORING (Top 15-20 Patterns)
        # ============================================
        if options.get('apply_priority', True):
            print("[UNIFIED] Stage 2: Priority refactoring (top 15 patterns)...")
            priority_result = apply_priority_refactorings(current_code)
            
            if priority_result.get('success'):
                current_code = priority_result.get('refactored_code', current_code)
                results['stages']['priority'] = {
                    'applied': True,
                    'patterns_applied': priority_result.get('patterns_applied', 0),
                    'changes': priority_result.get('changes', [])
                }
                results['all_changes'].extend(priority_result.get('changes', []))
                print(f"[UNIFIED]   ✅ Priority: {priority_result.get('patterns_applied', 0)} patterns")
            else:
                results['stages']['priority'] = {'applied': False, 'error': priority_result.get('error')}
                print(f"[UNIFIED]   ⚠️  Priority failed: {priority_result.get('error')}")
        
        # ============================================
        # STAGE 3: ADVANCED COMPREHENSIVE (100+ Patterns)
        # ============================================
        if options.get('apply_advanced', True):
            print("[UNIFIED] Stage 3: Advanced refactoring (100+ patterns)...")
            categories = options.get('categories')
            advanced_result = refactor_comprehensive(current_code, categories=categories)
            
            if advanced_result.get('success'):
                current_code = advanced_result.get('refactored_code', current_code)
                results['stages']['advanced'] = {
                    'applied': True,
                    'changes': advanced_result.get('changes', []),
                    'metrics': advanced_result.get('metrics', {}),
                    'categories': advanced_result.get('categories_applied', [])
                }
                results['all_changes'].extend(advanced_result.get('changes', []))
                print(f"[UNIFIED]   ✅ Advanced: {len(advanced_result.get('changes', []))} changes")
            else:
                results['stages']['advanced'] = {'applied': False, 'error': advanced_result.get('error')}
                print(f"[UNIFIED]   ⚠️  Advanced failed: {advanced_result.get('error')}")
        
        # ============================================
        # STAGE 4: PERFORMANCE OPTIMIZATION
        # ============================================
        if options.get('apply_performance', True):
            print("[UNIFIED] Stage 4: Performance optimization...")
            perf_result = optimize_performance(current_code)
            
            if perf_result.get('success'):
                # Performance optimizer may suggest changes but not always apply them
                if perf_result.get('refactored_code'):
                    current_code = perf_result.get('refactored_code', current_code)
                
                results['stages']['performance'] = {
                    'applied': True,
                    'optimizations': perf_result.get('optimizations', []),
                    'suggestions': perf_result.get('suggestions', [])
                }
                results['all_suggestions'].extend(perf_result.get('suggestions', []))
                print(f"[UNIFIED]   ✅ Performance: {len(perf_result.get('optimizations', []))} optimizations")
            else:
                results['stages']['performance'] = {'applied': False, 'error': perf_result.get('error')}
                print(f"[UNIFIED]   ⚠️  Performance failed: {perf_result.get('error')}")
        
        # ============================================
        # STAGE 5: RISK & RESOURCE REFACTORING (5 modules)
        # Lock, DB conn, timeout, list->set, caching, etc.
        # ============================================
        if options.get('apply_risk', True):
            print("[UNIFIED] Stage 5: Risk & Resource refactoring...")
            try:
                risk_result = refactor_risk_and_performance(current_code)
                
                if risk_result.get('refactored_code'):
                    current_code = risk_result.get('refactored_code', current_code)
                
                results['stages']['risk_resource'] = {
                    'applied': True,
                    'total_issues': risk_result.get('total_issues', 0),
                    'risk_score': risk_result.get('overall_risk_score', 0),
                    'perf_score': risk_result.get('overall_perf_score', 0),
                    'changes': risk_result.get('all_changes', [])
                }
                results['all_changes'].extend(risk_result.get('all_changes', []))
                print(f"[UNIFIED]   ✅ Risk/Resource: {risk_result.get('total_issues', 0)} issues found")
            except Exception as e:
                results['stages']['risk_resource'] = {'applied': False, 'error': str(e)}
                print(f"[UNIFIED]   ⚠️  Risk/Resource failed: {e}")
        
        # ============================================
        # STAGE 6: SECURITY AST REFACTORING (20 Bandit Patterns)
        # ============================================
        if options.get('apply_security', True):
            print("[UNIFIED] Stage 6: Security AST refactoring (20 Bandit patterns)...")
            try:
                security_result = run_security_refactoring(current_code)
                
                if security_result.get('refactored_code'):
                    current_code = security_result.get('refactored_code', current_code)
                
                results['stages']['security_ast'] = {
                    'applied': True,
                    'total_issues': security_result.get('total_issues', 0),
                    'total_fixes': security_result.get('total_fixes', 0),
                    'risk_score': security_result.get('risk_score', 0),
                    'vulnerability_summary': security_result.get('vulnerability_summary', {}),
                    'suggestions': security_result.get('suggestions', [])
                }
                results['all_changes'].extend(security_result.get('changes_applied', []))
                results['all_suggestions'].extend(security_result.get('suggestions', []))
                print(f"[UNIFIED]   ✅ Security: {security_result.get('total_issues', 0)} vulnerabilities, {security_result.get('total_fixes', 0)} fixes")
            except Exception as e:
                results['stages']['security_ast'] = {'applied': False, 'error': str(e)}
                print(f"[UNIFIED]   ⚠️  Security AST failed: {e}")
        
        # ============================================
        # ANALYSIS: Code Quality, Architecture, Best Practices, Ethics
        # ============================================
        print("[UNIFIED] Analysis: Code quality, architecture, best practices, ethics...")

        results['analysis']['code_quality'] = analyze_code(current_code)
        results['analysis']['best_practices'] = check_best_practices(current_code)
        results['analysis']['ethical'] = analyze_ethical_code(current_code)
        results['analysis']['structure'] = analyze_code_structure(current_code)
        results['analysis']['suggestions'] = suggest_refactorings(current_code)

        try:
            arch_result = analyze_architecture({'main.py': current_code})
            results['analysis']['architecture'] = arch_result
        except Exception as e:
            print(f"[UNIFIED]   ⚠️  Architecture analysis failed: {e}")
            results['analysis']['architecture'] = {'error': str(e)}

        print(f"[UNIFIED]   ✅ Analysis complete")
        
        # ============================================
        # FINAL RESULTS
        # ============================================
        results['refactored_code'] = current_code
        results['processing_time_ms'] = (time.time() - start_time) * 1000
        
        # Summary statistics
        results['summary'] = {
            'total_changes': len(results['all_changes']),
            'total_suggestions': len(results['all_suggestions']),
            'original_length': len(code),
            'refactored_length': len(current_code),
            'length_change': len(current_code) - len(code),
            'original_lines': len(code.splitlines()),
            'refactored_lines': len(current_code.splitlines()),
            'line_change': len(current_code.splitlines()) - len(code.splitlines()),
            'stages_applied': sum(1 for stage in results['stages'].values() if stage.get('applied')),
            'processing_time_ms': results['processing_time_ms']
        }
        
        print(f"[UNIFIED] ✅ COMPLETE - {len(results['all_changes'])} total changes in {results['processing_time_ms']:.0f}ms")
        
        return results
        
    except Exception as e:
        print(f"[UNIFIED] ❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        
        results['success'] = False
        results['error'] = str(e)
        results['refactored_code'] = code  # Return original on error
        results['processing_time_ms'] = (time.time() - start_time) * 1000
        
        return results


def get_all_available_patterns() -> Dict:
    """
    Get comprehensive list of ALL available refactoring patterns
    
    Returns:
        Dictionary with patterns from all modules
    """
    
    return {
        'basic_ast': {
            'description': 'Basic AST transformations',
            'patterns': [
                'Simplify Conditionals',
                'Extract Complex Expressions',
                'Improve Loops',
                'Remove Unused Variables',
                'Refactor Magic Numbers'
            ]
        },
        'priority': {
            'description': 'Top 15-20 priority patterns (most impactful)',
            'patterns': get_priority_patterns()
        },
        'advanced': {
            'description': '100+ comprehensive patterns across 12 categories',
            'patterns': list_all_patterns()
        },
        'performance': {
            'description': 'Performance optimization patterns',
            'patterns': [
                'Algorithm Optimization',
                'Data Structure Selection',
                'Loop Optimization',
                'Caching Opportunities',
                'Lazy Evaluation'
            ]
        }
    }


def validate_python_syntax(code: str) -> Dict:
    """
    Validate Python syntax
    
    Args:
        code: Python code to validate
    
    Returns:
        Validation result
    """
    try:
        ast.parse(code)
        return {
            'valid': True,
            'message': 'Valid Python syntax'
        }
    except SyntaxError as e:
        return {
            'valid': False,
            'error': str(e),
            'line': e.lineno,
            'offset': e.offset,
            'message': f'Syntax error at line {e.lineno}: {e.msg}'
        }
    except Exception as e:
        return {
            'valid': False,
            'error': str(e),
            'message': f'Parse error: {str(e)}'
        }
