# Generated by Django 2.2.3 on 2019-07-08 15:14
from django.db import migrations

standard_unit_list = [
    # ["ampere", "A", [["ampere", 1.0]]],
    # ["candela", "cd", [["candela", 1.0]]],
    # ["dimensionless", "", [["dimensionless", 1.0]]],
    # ["kelvin", "K", [["kelvin", 1.0]]],
    # ["kilogram", "kg", [["kilogram", 1.0]]],
    # ["metre", "m", [["metre", 1.0]]],
    # ["mole", "mol", [["mole", 1.0]]],
    # ["second", "s", [["second", 1.0]]],

    ["ampere", "A", []],
    ["candela", "cd", []],
    ["dimensionless", "", []],
    ["kelvin", "K", []],
    ["kilogram", "kg", []],
    ["metre", "m", []],
    ["mole", "mol", []],
    ["second", "s", []],

    ["becquerel", "Bq", [["second", -1.0]]],
    ["coulomb", "C", [["ampere", -1.0], ["second", 1.0]]],
    ["farad", "F", [["ampere", 2.0], ["kilogram", -1.0], ["metre", -2.0], ["second", -4.0]]],
    ["gram", "g", [["kilogram", 1.0]]],
    ["gray", "Gy", [["metre", 2.0], ["second", -2.0]]],
    ["henry", "H", [["ampere", -2.0], ["kilogram", 1.0], ["metre", 2.0], ["second", -2.0]]],
    ["hertz", "Hz", [["second", -1.0]]],
    ["joule", "J", [["kilogram", 1.0], ["metre", 2.0], ["second", -2.0]]],
    ["katal", "kat", [["mole", 1.0], ["second", -1.0]]],
    ["litre", "l", [["metre", 3.0]]],
    ["lumen", "lm", [["candela", 1.0]]],
    ["lux", "lx", [["candela", 1.0], ["metre", -2.0]]],
    ["newton", "N", [["kilogram", 1.0], ["metre", 1.0], ["second", -2.0]]],
    ["ohm", "&Omega;", [["ampere", -2.0], ["kilogram", 1.0], ["metre", 2.0], ["second", -3.0]]],
    ["pascal", "Pa", [["kilogram", 1.0], ["metre", -1.0], ["second", -2.0]]],
    ["radian", "rad", [["dimensionless", 1.0]]],
    ["siemens", "S", [["ampere", 2.0], ["kilogram", -1.0], ["metre", -2.0], ["second", 3.0]]],
    ["sievert", "Sv", [["metre", 2.0], ["second", -2.0]]],
    ["steradian", "sr", [["dimensionless", 1.0]]],
    ["tesla", "T", [["ampere", -1.0], ["kilogram", 1.0], ["second", -2.0]]],
    ["volt", "V", [["ampere", -1.0], ["kilogram", 1.0], ["metre", 2.0], ["second", -3.0]]],
    ["watt", "W", [["kilogram", 1.0], ["metre", 2.0], ["second", -3.0]]],
    ["weber", "Wb", [["ampere", -1.0], ["kilogram", 1.0], ["metre", 2.0], ["second", -2.0]]],

    ["liter", "l", [["litre", 1.0]]],
    ["meter", "m", [["metre", 1.0]]]
]

prefix_list = [
    ["yotta", 24, "Y"],
    ["zetta", 21, "Z"],
    ["exa", 18, "E"],
    ["peta", 15, "P"],
    ["tera", 12, "T"],
    ["giga", 9, "G"],
    ["mega", 6, "M"],
    ["kilo", 3, "k"],
    ["hecto", 2, "h"],
    ["deca", 1, "da"],
    ["", 0, ""],
    ["deci", -1, "d"],
    ["centi", -2, "c"],
    ["milli", -3, "m"],
    ["micro", -6, "&mu;"],
    ["nano", -9, "n"],
    ["pico", -12, "p"],
    ["femto", -15, "f"],
    ["atto", -18, "a"],
    ["zepto", -21, "z"],
    ["yocto", -24, "y"],
    ["24", 24, "(1e24)"],
    ["23", 23, "(1e23)"],
    ["22", 22, "(1e22)"],
    ["21", 21, "(1e21)"],
    ["20", 20, "(1e20)"],
    ["19", 19, "(1e19)"],
    ["18", 18, "(1e18)"],
    ["17", 17, "(1e17)"],
    ["16", 16, "(1e16)"],
    ["15", 15, "(1e15)"],
    ["14", 14, "(1e14)"],
    ["13", 13, "(1e13)"],
    ["12", 12, "(1e12)"],
    ["11", 11, "(1e11)"],
    ["10", 10, "(1e10)"],
    ["9", 9, "(1e09)"],
    ["8", 8, "(1e08)"],
    ["7", 7, "(1e07)"],
    ["6", 6, "(1e06)"],
    ["5", 5, "(1e05)"],
    ["4", 4, "(1e04)"],
    ["3", 3, "(1e03)"],
    ["2", 2, "(1e02)"],
    ["1", 1, "(1e1)"],
    ["0", 0, "(1e0)"],
    ["-1", -1, "(1e-1)"],
    ["-2", -2, "(1e-2)"],
    ["-3", -3, "(1e-3)"],
    ["-4", -4, "(1e-4)"],
    ["-5", -5, "(1e-5)"],
    ["-6", -6, "(1e-6)"],
    ["-7", -7, "(1e-7)"],
    ["-8", -8, "(1e-8)"],
    ["-9", -9, "(1e-9)"],
    ["-10", -10, "(1e-10)"],
    ["-11", -11, "(1e-11)"],
    ["-12", -12, "(1e-12)"],
    ["-13", -13, "(1e-13)"],
    ["-14", -14, "(1e-14)"],
    ["-15", -15, "(1e-15)"],
    ["-16", -16, "(1e-16)"],
    ["-17", -17, "(1e-17)"],
    ["-18", -18, "(1e-18)"],
    ["-19", -19, "(1e-19)"],
    ["-20", -20, "(1e-20)"],
    ["-21", -21, "(1e-21)"],
    ["-22", -22, "(1e-22)"],
    ["-23", -23, "(1e-23)"],
    ["-24", -24, "(1e-24)"]]

error_list = [
    ['4.2.1', 'Every model must have a name.'],
    ['4.2.3', 'A model must contain only one encapsulation element.'],
    ['8.1.1', 'Every units element must have an unprefixed name attribute, which must be a valid CellML identifier.'],
    ['8.1.2', 'The value of the units\' name attribute must be unique within this infoset.'],
    ['8.1.3', 'The value of the units\' name must not be the same as any of the built-in units.']
]


def add_administrator_accounts(apps, schema_editor):
    Person = apps.get_model('main', 'Person')
    User = apps.get_model('auth', 'User')

    user = User(username="admin")
    user.save()

    admin_person = Person(
        user=user,
        first_name="Admini",
        last_name="Strator",
        email="noEmail@noEmail.com",
    )
    admin_person.save()

    trash = User(username='trash')
    trash.save()

    trash_person = Person(
        user=trash,
        first_name='Recycle',
        last_name='Bin',
        email="noEmailEither@noEmail.com"
    )
    trash_person.save()


def add_error_codes(apps, schema_editor):
    CellMLSpecification = apps.get_model('main', 'CellMLSpecification')

    for row in error_list:
        e = CellMLSpecification(
            code=row[0],
            notes=row[1]
        )
        e.save()


def add_standards(apps, schema_editor):
    Unit = apps.get_model('main', 'Unit')
    CompoundUnit = apps.get_model('main', 'CompoundUnit')
    Prefix = apps.get_model('main', 'Prefix')
    Person = apps.get_model('main', 'Person')

    admin_person = Person.objects.get(user__username="admin")

    for name, value, symbol in prefix_list:
        prefix = Prefix(name=name, value=value, symbol=symbol)
        prefix.save()

    for name, symbol, made_of in standard_unit_list:
        cu = CompoundUnit(name=name, is_standard=True, symbol=symbol, privacy='public', owner=admin_person, is_valid=True)
        cu.save()
        for key, val in made_of:
            base = CompoundUnit.objects.filter(name=key).first()
            if base:
                u = Unit(exponent=val, parent_cu=cu, child_cu=base, reference=key, privacy='public', owner=admin_person)
                u.save()


def remove_standards(apps, schema_editor):
    Unit = apps.get_model('main', 'Unit')
    CompoundUnit = apps.get_model('main', 'CompoundUnit')
    Prefix = apps.get_model('main', 'Prefix')

    for name, symbol, made_of in standard_unit_list:
        try:
            cu = CompoundUnit.objects.get(name=name, is_standard=True)

            for u in cu.units.all():
                u.delete()

            cu.delete()
        except:
            pass

    for p in prefix_list:
        try:
            prefix = Prefix.objects.get(name=p[0])
            prefix.delete()
        except:
            pass


def remove_error_codes(apps, schema_editor):
    ValidatorMessages = apps.get_model('main', 'ValidatorMessages')

    for e in ValidatorMessages.objects.all():
        try:
            e.delete()
        except:
            pass


def remove_administrator_accounts(apps, schema_editor):
    Person = apps.get_model('main', 'Person')
    User = apps.get_model('auth', 'User')
    try:
        u = User.objects.get(username='admin')
        a = u.person
        a.delete()
        u.delete()
    except:
        pass

    try:
        u = User.objects.get(username='trash')
        a = u.person
        a.delete()
        u.delete()
    except:
        pass


def forwards_stuff(apps, schema_editor):
    add_administrator_accounts(apps, schema_editor)
    add_standards(apps, schema_editor)


def backwards_stuff(apps, schema_editor):
    remove_standards(apps, schema_editor)
    remove_administrator_accounts(apps, schema_editor)


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(code=forwards_stuff, reverse_code=backwards_stuff),
    ]
