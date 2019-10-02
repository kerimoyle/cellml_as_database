"""
This is a simple map which allows us to use different model class names here than are used in the CellML files.
"""
MODEL_NAME_DICT = {
    'component': 'component',
    'encapsulation': 'encapsulation',
    'math': 'math',
    'model': 'cellmodel',
    'reset': 'reset',
    'unit': 'unit',
    'units': 'compoundunit',
    'variable': 'variable',
}

DOWNSTREAM_VALIDATION_DICT = {
    'cellmodel': ['encapsulated_components', 'compoundunits'],
    'component': ['child_components', 'variables', 'maths', 'resets'],
    'compoundunit': [],
    'variable': [],
    'math': [],
    'encapsulation': [],
    'unit': [],
    'reset': []
}

LOCAL_DICT = {
    'cellmodel': ['name', 'cellml_id'],
    'component': ['name'],
    'compoundunit': ['name'],
    'variable': ['name', 'cellml_id', 'initial_value_constant'],
    'math': [],
    'encapsulation': [],
    'reset': ['name', 'order']
}

FOREIGN_DICT = {
    'cellmodel': [],
    'component': [],
    'compoundunit': [],
    'variable': ['initial_value_variable', 'compoundunit', 'component'],
    'math': [],
    'encapsulation': [],
    'reset': ['component', 'variable', 'test_variable', 'test_value', 'reset_value']
}

DISPLAY_DICT = {
    'component': {
        'summary_template': 'main/tab_summary_nochildren.html',
        'validity_template': 'main/tab_validity.html',
        'tabs': [
            {'field': 'child_components', 'obj_type': 'component', 'title': 'Encapsulated components',
             'template': 'main/tab_default.html', 'related_name': 'parent_component'},
            {'field': 'variables', 'obj_type': 'variable', 'title': 'Variables',
             'template': 'main/tab_default.html', 'related_name': 'component'},
            {'field': 'maths', 'obj_type': 'math', 'title': 'Maths', 'template': 'main/tab_default.html',
             'related_name': 'component'},
            {'field': 'resets', 'obj_type': 'reset', 'title': 'Resets', 'template': 'main/tab_default.html',
             'related_name': 'component'},
        ],
        'foreign_keys': [
            {'field': 'parent_component', 'obj_type': 'component', 'title': 'parent encapsulating component'},
            {'field': 'model', 'obj_type': 'cellmodel', 'title': 'parent model'},
        ],
        'present_in': [
            # {'field': 'models', 'obj_type': 'cellmodel', 'title': 'Models'},
        ]
    },

    'math': {
        'summary_template': 'main/tab_maths.html',
        'validity_template': 'main/tab_validity.html',
        'tabs': [
            {'field': 'components', 'obj_type': 'component', 'title': 'Parent components',
             'template': 'main/tab_default.html', 'related_name': 'parent_component'},
        ],
        'foreign_keys': [

        ],
        'present_in': [
            {'field': 'components', 'obj_type': 'component', 'title': 'parent component'},
        ]
    },

    'variable': {
        'summary_template': 'main/tab_summary_nochildren.html',
        'validity_template': 'main/tab_validity.html',
        'tabs': [
            {'field': 'equivalent_variables', 'obj_type': 'variable', 'title': 'Equivalent variables',
             'template': 'main/tab_default.html', 'related_name': 'equivalent_variables'},
            {'field': 'reset_variables', 'obj_type': 'reset', 'title': 'Variable is reset by',
             'template': 'main/tab_reset.html', 'related_name': 'variable'},
            {'field': 'reset_test_variables', 'obj_type': 'reset', 'title': 'Variable will reset',
             'template': 'main/tab_reset.html', 'related_name': 'test_variable'},
        ],
        'present_in': [

        ],
        'foreign_keys': [
            {'field': 'initial_value_variable', 'obj_type': 'variable', 'title': 'initial_value_variable'},
            {'field': 'compoundunit', 'obj_type': 'compoundunit', 'title': 'compoundunit'},
            {'field': 'component', 'obj_type': 'component', 'title': 'component'},
        ]
    },

    'reset': {
        'summary_template': 'main/tab_summary_nochildren.html',
        'validity_template': None,
        'tabs': [],
        'present_in': [],
        'foreign_keys': [
            {'field': 'component', 'obj_type': 'component', 'title': 'component'},
            {'field': 'variable', 'obj_type': 'variable', 'title': 'variable'},
            {'field': 'test_variable', 'obj_type': 'variable', 'title': 'test variable'},
            {'field': 'test_value', 'obj_type': 'math', 'title': 'test value'},
            {'field': 'reset_value', 'obj_type': 'math', 'title': 'reset value'},
        ],
    },

    'compoundunit': {
        'summary_template': 'main/tab_summary_nochildren.html',
        'validity_template': 'main/tab_validity.html',
        'tabs': [
            {'field': 'product_of', 'obj_type': 'compoundunit', 'title': 'Product of',
             'template': 'main/tab_childunits.html', 'related_name': 'parent_cu'},
            {'field': 'part_of', 'obj_type': 'compoundunit', 'title': 'Used in units',
             'template': 'main/tab_parentunits.html', 'related_name': 'child_cu'},
            {'field': 'models', 'obj_type': 'cellmodel', 'title': 'Used in models',
             'template': 'main/tab_fyi.html', 'related_name': 'compoundunits'},
            # {'field': 'variables', 'obj_type': 'variable', 'title': 'Used by variables',
            #  'template': 'main/tab_fyi.html', 'related_name': 'compoundunit'},
        ],
        'present_in': [],
        'foreign_keys': []
    },

    'cellmodel': {
        'summary_template': 'main/tab_summary_nochildren.html',
        'validity_template': 'main/tab_validity.html',
        'tabs': [
            {'field': 'encapsulated_components', 'obj_type': 'component', 'title': 'Encapsulated components',
             'template': 'main/tab_default.html'},
            {'field': 'compoundunits', 'obj_type': 'compoundunit', 'title': 'Units',
             'template': 'main/tab_compoundunits.html'},
        ],
        'present_in': [],
        'foreign_keys': [],
    }
}

MODEL_CLASSES = {
    'cellmodel': 'model',
    # 'encapsulation': 'encapsulation',
    'component': 'component',
    'math': 'maths',
    'compoundunit': 'compound unit',
    # 'unit': 'unit',
    'variable': 'variable',
    'reset': 'reset',
}

MENU_OPTIONS = {
    'create': {
        'create': MODEL_CLASSES,
        'browse': MODEL_CLASSES,
    },
    'display': {
        'create': MODEL_CLASSES,
        'browse': MODEL_CLASSES,
    },
    'edit': {
        'create': MODEL_CLASSES,
        'browse': MODEL_CLASSES,
    },
    'home': {
        'create': MODEL_CLASSES,
        'browse': MODEL_CLASSES,
    },
    'upload': {
        'create': MODEL_CLASSES,
        'browse': MODEL_CLASSES,
    },
    '': {
        'create': MODEL_CLASSES,
        'browse': MODEL_CLASSES,
    }
}

KIND_DICT = {
    'COMPONENT': 'component',
    'CONNECTION': '',
    'ENCAPSULATION': '',
    'IMPORT': '',
    'MATHML': 'math',
    'MODEL': 'cellmodel',
    'UNDEFINED': '',
    'UNITS': 'compoundunit',
    'VARIABLE': 'variable',
    'XML': ''
}

BREADCRUMB_DICT = {
    'cellmodel': None,
    'model': None,
    'component': ['cellmodel'],
    'variable': ['component', 'cellmodel'],
    'compoundunit': ['cellmodel'],
    'reset': ['component', 'cellmodel'],
    'encapsulation': ['cellmodel']
}
