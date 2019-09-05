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

DISPLAY_DICT = {
    'component':
        {
            'tabs': [
                {'field': 'variables', 'obj_type': 'variable', 'title': 'Variables'},
                {'field': 'maths', 'obj_type': 'maths', 'title': 'Maths'},
                {'field': 'resets', 'obj_type': 'reset', 'title': 'Resets'}
            ],
            'present_in':
                [
                    {'field': 'models', 'obj_type': 'cellmodel', 'title': 'Models'},
                ]
        },

    'variable':
        {
            'tabs': [
                {'field': 'equivalent_variables', 'obj_type': 'variable', 'title': 'Equivalent variables'},

            ],
            'present_in':
                [
                    {'field': 'component', 'obj_type': 'component', 'title': 'Component'},
                    {'field': 'compoundunit', 'obj_type': 'compoundunit', 'title': 'Units'},

                ],
        },
    'reset': [

    ],
    'compoundunit': [

    ],
    'cellmodel': {
        'tabs': [
            {'field': 'components', 'obj_type': 'component', 'title': 'Components'},
            {'field': 'compoundunits', 'obj_type': 'compoundunit', 'title': 'Units'},
        ],
        'present_in':[]
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
