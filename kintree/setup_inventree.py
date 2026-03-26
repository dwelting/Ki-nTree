import sys

from .config import settings
from .common.tools import cprint
from .config import config_interface
from .database import inventree_api, inventree_interface


def setup_inventree():
    SETUP_CATEGORIES = False
    SETUP_PARAMETERS = False
    SETUP_CATEGORY_PARAMETERS = True

    def create_categories(parent, name, categories):
        category_pk, is_category_new = inventree_api.create_category(parent=parent, name=name)
        if is_category_new:
            cprint(f'[TREE]\tSuccess: Category "{name}" was added to InvenTree')
        else:
            cprint(f'[TREE]\tWarning: Category "{name}" already exists')

        if isinstance(categories[name], dict):
            for cat in categories[name]:
                if cat == "__type__":
                    continue
                create_categories(parent=name, name=cat, categories=categories[name])

    if SETUP_CATEGORIES or SETUP_PARAMETERS or SETUP_CATEGORY_PARAMETERS:
        cprint('\n[MAIN]\tStarting InvenTree setup', silent=settings.SILENT)
        # Load category configuration file
        categories = config_interface.load_file(settings.CONFIG_CATEGORIES)['CATEGORIES']

        cprint('[MAIN]\tConnecting to Inventree', silent=settings.SILENT)
        inventree_connect = inventree_interface.connect_to_server()

        if not inventree_connect:
            sys.exit(-1)

        # Setup database for test
        inventree_api.set_inventree_db_test_mode()

    if SETUP_CATEGORIES:
        for category in categories.keys():
            cprint(f'\n[MAIN]\tCreating categories in {category.upper()}')
            create_categories(parent=None, name=category, categories=categories)

    if SETUP_PARAMETERS:
        # Load parameter configuration file
        parameters = config_interface.load_file(settings.CONFIG_PARAMETERS)
        # cprint(parameters)
        cprint('\n[MAIN]\tLoading Parameters')
        for name, unit in parameters.items():
            pk = inventree_api.create_parameter_template(name, unit)
            if pk > 0:
                cprint(f'[TREE]\tSuccess: Parameter "{name}" was added to InvenTree')
            else:
                cprint(f'[TREE]\tWarning: Parameter "{name}" already exists')

    def set_category_parameter(name, categories, category_tree, supplier_parameters, parameters):
        if not categories[name]:
            return

        category_parameter = None
        if isinstance(categories[name], dict) and "__type__" in categories[name]:
            category_parameter = categories[name]["__type__"]
        elif isinstance(categories[name], str):
            category_parameter = categories[name]

        category_tree.append(name)
        if category_parameter:
            if category_parameter in supplier_parameters.keys():
                category_id = inventree_api.get_inventree_category_id(category_tree)
                for parameter in supplier_parameters[category_parameter]:
                    if parameter in parameters.keys():
                        if inventree_api.set_category_parameter(name, category_id, parameter):
                            cprint(f'[TREE]\tSuccess: Category parameter "{parameter}" was added to {name}')
                        else:
                            cprint(f'[TREE]\tWarning: Category parameter "{parameter}" in category {name} already exists')

        if isinstance(categories[name], dict):
            for cat in categories[name]:
                if cat == "__type__":
                    continue
                if len(category_tree) > 1:
                    category_tree.pop()
                set_category_parameter(name=cat, categories=categories[name], category_tree=category_tree, supplier_parameters=supplier_parameters, parameters=parameters)

    if SETUP_CATEGORY_PARAMETERS:
        supplier_parameters = config_interface.load_file(settings.CONFIG_SUPPLIER_PARAMETERS)
        parameters = config_interface.load_file(settings.CONFIG_PARAMETERS)

        for category in categories.keys():
            cprint(f'\n[MAIN]\tCreating category parameters in {category.upper()}')
            set_category_parameter(name=category, categories=categories, category_tree=list(), supplier_parameters=supplier_parameters, parameters=parameters)


if __name__ == '__main__':
    setup_inventree()
