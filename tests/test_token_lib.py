# -*- coding: utf-8 -*-
import sys
import time

sys.path.extend(["../"])
from bbc1.lib import id_lib, token_lib
from bbc1.lib.app_support_lib import TransactionLabel
from bbc1.core import bbc_app
from bbc1.core import bbclib
from bbc1.core.bbc_config import DEFAULT_CORE_PORT


domain_id = None
mint_id = None
mint_id_counter = None
idPubkeyMap = None
keypairs = None
keypairs_counter = None


def setup():
    global domain_id
    global mint_id
    global mint_id_counter
    global idPubkeyMap
    global keypairs
    global keypairs_counter

    domain_id = bbclib.get_new_id("test_token_lib", include_timestamp=False)

    #tmpclient = bbc_app.BBcAppClient(port=DEFAULT_CORE_PORT, loglevel="all")
    tmpclient = bbc_app.BBcAppClient(port=DEFAULT_CORE_PORT, multiq=False, loglevel="all")
    #tmpclient.domain_setup(domain_id, "simple_cluster")
    tmpclient.domain_setup(domain_id)
    tmpclient.callback.synchronize()
    tmpclient.unregister_from_core()

    idPubkeyMap = id_lib.BBcIdPublickeyMap(domain_id)
    mint_id, keypairs = idPubkeyMap.create_user_id(num_pubkeys=1)
    mint_id_counter, keypairs_counter = idPubkeyMap.create_user_id(
            num_pubkeys=1)


def test_fraction():

    frac = token_lib.Fraction(2, 3)

    assert frac.numerator == 2
    assert frac.denominator == 3
    assert frac.is_positive_or_zero() == True

    frac = token_lib.Fraction('-1/100')

    assert frac.numerator == -1
    assert frac.denominator == 100
    assert frac.is_positive_or_zero() == False

    dat = frac.serialize()
    idx, frac = token_lib.Fraction.from_serialized_data(0, dat)

    assert idx == 1 + 2 + 2
    assert frac.numerator == -1
    assert frac.denominator == 100

    frac = token_lib.Fraction(4, 5)

    dat = frac.serialize()
    _, frac = token_lib.Fraction.from_serialized_data(0, dat)

    assert frac.numerator == 4
    assert frac.denominator == 5

    frac = frac * token_lib.Fraction(2, 3)

    assert frac.numerator == 8
    assert frac.denominator == 15

    v = frac * 100

    assert v == 53

    try:
        v = frac * '100'
    except TypeError:
        v = 1

    assert v == 1

    frac = frac + 1

    assert frac.numerator == 23
    assert frac.denominator == 15

    frac = frac ** 2

    assert frac.numerator == 529
    assert frac.denominator == 225

    try:
        frac = frac ** '100'
    except TypeError:
        v = 10

    assert v == 10


def test_variation():

    rate = token_lib.Fraction(-1, 10)
    rate_to_stop = token_lib.Fraction(1, 2)
    time_unit = 60 * 60 * 24 * 7
    expire_after = 60 * 60 * 24 * 30

    vari = token_lib.Variation(0, token_lib.Variation.T_SIMPLE, rate,
                                rate_to_stop, time_unit, expire_after)
    vari0 = vari

    dat = vari.serialize()
    idx, vari = token_lib.Variation.from_serialized_data(0, dat)

    assert idx == 1 + 1 + 5 + 5 + 8 + 8
    assert vari.condition == 0
    assert vari.type == token_lib.Variation.T_SIMPLE
    assert vari.rate == rate
    assert vari.rate_to_stop == rate_to_stop
    assert vari.time_unit == time_unit
    assert vari.expire_after == expire_after

    assert vari == vari0


def test_value_asset_body():

    rate = token_lib.Fraction(-1, 100)
    rate_to_stop = token_lib.Fraction(1, 3)
    time_unit = 60 * 60 * 24 * 30
    expire_after = 60 * 60 * 24 * 180

    vari = token_lib.Variation(0, token_lib.Variation.T_SIMPLE, rate,
                                rate_to_stop, time_unit, expire_after)
    body = token_lib.ValueAssetBody(100, 12345, [vari])

    dat = body.serialize()
    _, body = token_lib.BaseAssetBody.from_serialized_data(0, dat)

    assert body.type == token_lib.BaseAssetBody.T_VALUE
    assert body.value_specified == 100
    assert body.time_of_origin == 12345
    assert body.variation_specs[0].condition == vari.condition
    assert body.variation_specs[0].type == vari.type
    assert body.variation_specs[0].rate == vari.rate
    assert body.variation_specs[0].rate_to_stop == vari.rate_to_stop
    assert body.variation_specs[0].time_unit == vari.time_unit
    assert body.variation_specs[0].expire_after == vari.expire_after


def test_asset_body_types():

    rate = token_lib.Fraction(-1, 100)
    rate_to_stop = token_lib.Fraction(1, 3)
    time_unit = 60 * 60 * 24 * 30
    expire_after = 60 * 60 * 24 * 180

    vari = token_lib.Variation(0, token_lib.Variation.T_SIMPLE, rate,
                                rate_to_stop, time_unit, expire_after)
    body = token_lib.ValueAssetBody(100, 12345, [vari])

    dat = body.serialize()
    _, body = token_lib.BaseAssetBody.from_serialized_data(0, dat)

    assert body.type == token_lib.BaseAssetBody.T_VALUE

    body = token_lib.ChangeAssetBody(100, 12345, [vari])

    dat = body.serialize()
    _, body = token_lib.BaseAssetBody.from_serialized_data(0, dat)

    assert body.type == token_lib.BaseAssetBody.T_CHANGE

    body = token_lib.IssuedAssetBody(100, 12345, [vari])

    dat = body.serialize()
    _, body = token_lib.BaseAssetBody.from_serialized_data(0, dat)

    assert body.type == token_lib.BaseAssetBody.T_ISSUED


def test_effective_value():

    rate = token_lib.Fraction(-1, 10)
    rate_to_stop = token_lib.Fraction(1, 2)
    time_unit = 100
    expire_after = 0

    vari = token_lib.Variation(0, token_lib.Variation.T_SIMPLE, rate,
                rate_to_stop, time_unit, expire_after)
    body = token_lib.ValueAssetBody(100, 10, [vari])

    assert body.get_effective_value(0) == 100
    assert body.get_effective_value(100) == 100
    assert body.get_effective_value(110) == 90
    assert body.get_effective_value(120) == 90
    assert body.get_effective_value(510) == 50
    assert body.get_effective_value(520) == 50
    assert body.get_effective_value(610) == 50
    assert body.get_effective_value(10000) == 50

    rate = token_lib.Fraction(1, 10)
    rate_to_stop = token_lib.Fraction(2, 1)

    vari = token_lib.Variation(0, token_lib.Variation.T_SIMPLE, rate,
                                rate_to_stop, time_unit, expire_after)
    body = token_lib.ValueAssetBody(100, 10, [vari])

    assert body.get_effective_value(0) == 100
    assert body.get_effective_value(100) == 100
    assert body.get_effective_value(110) == 110
    assert body.get_effective_value(120) == 110
    assert body.get_effective_value(1010) == 200
    assert body.get_effective_value(1020) == 200
    assert body.get_effective_value(1110) == 200
    assert body.get_effective_value(10000) == 200

    rate = token_lib.Fraction(-1, 10)
    rate_to_stop = token_lib.Fraction(0, 1)

    vari = token_lib.Variation(0, token_lib.Variation.T_SIMPLE, rate,
                                rate_to_stop, time_unit, expire_after)
    body = token_lib.ValueAssetBody(100, 10, [vari])

    assert body.get_effective_value(0) == 100
    assert body.get_effective_value(100) == 100
    assert body.get_effective_value(110) == 90
    assert body.get_effective_value(120) == 90
    assert body.get_effective_value(1010) == 0
    assert body.get_effective_value(1020) == 0
    assert body.get_effective_value(1110) == 0
    assert body.get_effective_value(10000) == 0

    vari = token_lib.Variation(0, token_lib.Variation.T_COMPOUND, rate,
                                rate_to_stop, time_unit, expire_after)
    body = token_lib.ValueAssetBody(100, 10, [vari])

    assert body.get_effective_value(0) == 100
    assert body.get_effective_value(100) == 100
    assert body.get_effective_value(110) == 90
    assert body.get_effective_value(120) == 90
    assert body.get_effective_value(210) == 81
    assert body.get_effective_value(310) == 72
    assert body.get_effective_value(410) == 65

    vari = token_lib.Variation()
    body = token_lib.ValueAssetBody(100, 10, [vari])

    assert body.get_effective_value(0) == 100
    assert body.get_effective_value(100) == 100
    assert body.get_effective_value(110) == 100
    assert body.get_effective_value(120) == 100
    assert body.get_effective_value(10000) == 100

    vari = token_lib.Variation(type=token_lib.Variation.T_COMPOUND)
    body = token_lib.ValueAssetBody(100, 10, [vari])

    assert body.get_effective_value(0) == 100
    assert body.get_effective_value(100) == 100
    assert body.get_effective_value(110) == 100
    assert body.get_effective_value(120) == 100
    assert body.get_effective_value(10000) == 100

    vari = token_lib.Variation(expire_after=500)
    body = token_lib.ValueAssetBody(100, 10, [vari])

    assert body.get_effective_value(0) == 100
    assert body.get_effective_value(100) == 100
    assert body.get_effective_value(110) == 100
    assert body.get_effective_value(120) == 100
    assert body.get_effective_value(509) == 100
    assert body.get_effective_value(510) == 0
    assert body.get_effective_value(10000) == 0

    body = token_lib.ValueAssetBody(100, 10, [])

    assert body.get_effective_value(0) == 100
    assert body.get_effective_value(510) == 100
    assert body.get_effective_value(10000) == 100


# FIXME: test_next_update_time


# FIXME: test_expected_loss_or_gain


def test_currency_spec():

    rate = token_lib.Fraction(-1, 10)
    rate_to_stop = token_lib.Fraction(1, 2)
    time_unit = 100
    expire_after = 0

    name = "Japanese Yen"
    symbol = "JPY"
    decimal = 2

    currency_spec_dict = {
        'name': name,
        'symbol': symbol,
        'decimal': decimal,
        'variation_specs': [
            {
                'condition': 0,
                'variation_type': "simple",
                'rate': "0",
                'rate_to_stop': "1/1",
                'time_unit': 0x7fffffffffffffff,
                'expire_after': 0,
            },
            {
                'condition': 1,
                'variation_type': "simple",
                'rate': "-1/100",
                'rate_to_stop': "0",
                'time_unit': 60*60*24*30,
                'expire_after': 60*60*24*180,
            },
        ],
        'option_witnesses_required': True,
        'option_expiration_rebased': True,
        'option_conditions_irreversible': False,
    }

    spec = token_lib.CurrencySpec(currency_spec_dict)

    assert spec.name == name
    assert spec.symbol == symbol
    assert spec.decimal == decimal

    assert len(spec.variation_specs) == 2

    assert spec.variation_specs[0].condition == 0
    assert spec.variation_specs[0].type == token_lib.Variation.T_SIMPLE
    assert spec.variation_specs[0].rate == 0
    assert spec.variation_specs[0].rate_to_stop == 1
    assert spec.variation_specs[0].time_unit == 0x7fffffffffffffff
    assert spec.variation_specs[0].expire_after == 0
    
    assert spec.variation_specs[1].condition == 1
    assert spec.variation_specs[1].type == token_lib.Variation.T_SIMPLE
    assert spec.variation_specs[1].rate == token_lib.Fraction("-1/100")
    assert spec.variation_specs[1].rate_to_stop == 0
    assert spec.variation_specs[1].time_unit == 60*60*24*30
    assert spec.variation_specs[1].expire_after == 60*60*24*180

    assert spec.option_witnesses_required == True
    assert spec.option_expiration_rebased == True
    assert spec.option_conditions_irreversible == False

    spec1 = token_lib.CurrencySpec(currency_spec_dict)

    assert spec1 == spec

    dat = spec1.serialize()
    _, spec2 = token_lib.CurrencySpec.from_serialized_data(0, dat)

    assert spec2 == spec1 == spec

    currency_spec_dict = {
        'name': "Whatever",
        'symbol': "WTV",
    }

    spec = token_lib.CurrencySpec(currency_spec_dict)

    assert not spec2 == spec

    assert spec.decimal == 0
    assert len(spec.variation_specs) == 0
    assert spec.option_witnesses_required == False
    assert spec.option_expiration_rebased == False
    assert spec.option_conditions_irreversible == True

    currency_spec_dict = {
        'name': 123,
        'symbol': symbol,
    }

    try:
        spec = token_lib.CurrencySpec(currency_spec_dict)
    except TypeError:
        spec = 10

    assert spec == 10

    currency_spec_dict = {
        'name': "US Dollar",
        'symbol': 31,
    }

    try:
        spec = token_lib.CurrencySpec(currency_spec_dict)
    except TypeError:
        spec = 1

    assert spec == 1

    currency_spec_dict = {
        'name': "US Dollar",
        'symbol': "USD",
        'decimal': "2",
    }

    try:
        spec = token_lib.CurrencySpec(currency_spec_dict)
    except TypeError:
        spec = 13

    assert spec == 13

    currency_spec_dict = {
        'name': "US Dollar",
        'symbol': "USD",
        'decimal': -1,
    }

    try:
        spec = token_lib.CurrencySpec(currency_spec_dict)
    except TypeError:
        spec = 14

    assert spec == 14

    currency_spec_dict = {
        'name': "US Dollar",
        'symbol': "USD",
        'decimal': 13,
    }

    try:
        spec = token_lib.CurrencySpec(currency_spec_dict)
    except TypeError:
        spec = 15

    assert spec == 15

    currency_spec_dict = {
        'name': name,
        'symbol': symbol,
        'variation_specs': [
            {
                'condition': 0,
                'variation_type': "simple",
                'rate': "0",
                'rate_to_stop': "1/1",
                'time_unit': 0x7fffffffffffffff,
                'expire_after': 0,
            }
        ],
    }

    try:
        spec = token_lib.CurrencySpec(currency_spec_dict)
    except TypeError:
        spec = 16

    assert not spec == 16
    assert len(spec.variation_specs) == 1

    currency_spec_dict = {
        'name': name,
        'symbol': symbol,
        'variation_specs': [
            {
                'condition': "0",
                'variation_type': "simple",
                'rate': "0",
                'rate_to_stop': "1/1",
                'time_unit': 0x7fffffffffffffff,
                'expire_after': 0,
            }
        ],
    }

    try:
        spec = token_lib.CurrencySpec(currency_spec_dict)
    except TypeError:
        spec = 17

    assert spec == 17

    currency_spec_dict = {
        'name': name,
        'symbol': symbol,
        'variation_specs': [
            {
                'condition': -1,
                'variation_type': "simple",
                'rate': "0",
                'rate_to_stop': "1/1",
                'time_unit': 0x7fffffffffffffff,
                'expire_after': 0,
            }
        ],
    }

    try:
        spec = token_lib.CurrencySpec(currency_spec_dict)
    except TypeError:
        spec = 18

    assert spec == 18

    currency_spec_dict = {
        'name': name,
        'symbol': symbol,
        'variation_specs': [
            {
                'condition': 128,
                'variation_type': "simple",
                'rate': "0",
                'rate_to_stop': "1/1",
                'time_unit': 0x7fffffffffffffff,
                'expire_after': 0,
            }
        ],
    }

    try:
        spec = token_lib.CurrencySpec(currency_spec_dict)
    except TypeError:
        spec = 19

    assert spec == 19

    currency_spec_dict = {
        'name': name,
        'symbol': symbol,
        'variation_specs': [
            {
                'condition': 0,
                'variation_type': 4,
                'rate': "0",
                'rate_to_stop': "1/1",
                'time_unit': 0x7fffffffffffffff,
                'expire_after': 0,
            }
        ],
    }

    try:
        spec = token_lib.CurrencySpec(currency_spec_dict)
    except TypeError:
        spec = 20

    assert spec == 20

    currency_spec_dict = {
        'name': name,
        'symbol': symbol,
        'variation_specs': [
            {
                'condition': 0,
                'variation_type': "exact",
                'rate': "0",
                'rate_to_stop': "1/1",
                'time_unit': 0x7fffffffffffffff,
                'expire_after': 0,
            }
        ],
    }

    try:
        spec = token_lib.CurrencySpec(currency_spec_dict)
    except TypeError:
        spec = 21

    assert spec == 21

    currency_spec_dict = {
        'name': name,
        'symbol': symbol,
        'variation_specs': [
            {
                'condition': 0,
                'variation_type': "simple",
                'rate': "1/32768",
                'rate_to_stop': "1/1",
                'time_unit': 0x7fffffffffffffff,
                'expire_after': 0,
            }
        ],
    }

    try:
        spec = token_lib.CurrencySpec(currency_spec_dict)
    except TypeError:
        spec = 22

    assert spec == 22

    currency_spec_dict = {
        'name': name,
        'symbol': symbol,
        'variation_specs': [
            {
                'condition': 0,
                'variation_type': "simple",
                'rate': "32768/32761",
                'rate_to_stop': "1/1",
                'time_unit': 0x7fffffffffffffff,
                'expire_after': 0,
            }
        ],
    }

    try:
        spec = token_lib.CurrencySpec(currency_spec_dict)
    except TypeError:
        spec = 23

    assert spec == 23

    currency_spec_dict = {
        'name': name,
        'symbol': symbol,
        'variation_specs': [
            {
                'condition': 0,
                'variation_type': "simple",
                'rate': "1/100",
                'rate_to_stop': "32768/32761",
                'time_unit': 0x7fffffffffffffff,
                'expire_after': 0,
            }
        ],
    }

    try:
        spec = token_lib.CurrencySpec(currency_spec_dict)
    except TypeError:
        spec = 24

    assert spec == 24

    currency_spec_dict = {
        'name': name,
        'symbol': symbol,
        'variation_specs': [
            {
                'condition': 0,
                'variation_type': "simple",
                'rate': "-1/100",
                'rate_to_stop': "2/1",
                'time_unit': 0x7fffffffffffffff,
                'expire_after': 0,
            }
        ],
    }

    try:
        spec = token_lib.CurrencySpec(currency_spec_dict)
    except TypeError:
        spec = 25

    assert spec == 25

    currency_spec_dict = {
        'name': name,
        'symbol': symbol,
        'variation_specs': [
            {
                'condition': 0,
                'variation_type': "simple",
                'rate': "-1/100",
                'rate_to_stop': "32761/32768",
                'time_unit': 0x7fffffffffffffff,
                'expire_after': 0,
            }
        ],
    }

    try:
        spec = token_lib.CurrencySpec(currency_spec_dict)
    except TypeError:
        spec = 26

    assert spec == 26

    currency_spec_dict = {
        'name': name,
        'symbol': symbol,
        'variation_specs': [
            {
                'condition': 0,
                'variation_type': "simple",
                'rate': "1/100",
                'rate_to_stop': "1/2",
                'time_unit': 0x7fffffffffffffff,
                'expire_after': 0,
            }
        ],
    }

    try:
        spec = token_lib.CurrencySpec(currency_spec_dict)
    except TypeError:
        spec = 27

    assert spec == 27

    currency_spec_dict = {
        'name': name,
        'symbol': symbol,
        'variation_specs': [
            {
                'condition': 0,
                'variation_type': "simple",
                'rate': "-1/100",
                'rate_to_stop': "1/2",
                'time_unit': 0x8fffffffffffffff,
                'expire_after': 0,
            }
        ],
    }

    try:
        spec = token_lib.CurrencySpec(currency_spec_dict)
    except TypeError:
        spec = 28

    assert spec == 28

    currency_spec_dict = {
        'name': name,
        'symbol': symbol,
        'variation_specs': [
            {
                'condition': 0,
                'variation_type': "simple",
                'rate': "-1/100",
                'rate_to_stop': "1/2",
                'time_unit': -1,
                'expire_after': 0,
            }
        ],
    }

    try:
        spec = token_lib.CurrencySpec(currency_spec_dict)
    except TypeError:
        spec = 29

    assert spec == 29

    currency_spec_dict = {
        'name': name,
        'symbol': symbol,
        'variation_specs': [
            {
                'condition': 0,
                'variation_type': "simple",
                'rate': "-1/100",
                'rate_to_stop': "1/2",
                'time_unit': 0x7fffffffffffffff,
                'expire_after': -1,
            }
        ],
    }

    try:
        spec = token_lib.CurrencySpec(currency_spec_dict)
    except TypeError:
        spec = 30

    assert spec == 30

    currency_spec_dict = {
        'name': name,
        'symbol': symbol,
        'variation_specs': [
            {
                'condition': 0,
                'variation_type': "simple",
                'rate': "-1/100",
                'rate_to_stop': "1/2",
                'time_unit': 0x7fffffffffffffff,
                'expire_after': 0x8000000000000000,
            }
        ],
    }

    try:
        spec = token_lib.CurrencySpec(currency_spec_dict)
    except TypeError:
        spec = 31

    assert spec == 31

    currency_spec_dict = {
        'name': name,
        'symbol': symbol,
        'option_witnesses_required': "yes",
        'option_expiration_rebased': True,
        'option_conditions_irreversible': False,
    }

    try:
        spec = token_lib.CurrencySpec(currency_spec_dict)
    except TypeError:
        spec = 31.5

    assert spec == 31.5

    currency_spec_dict = {
        'name': name,
        'symbol': symbol,
        'option_witnesses_required': "yes",
        'option_expiration_rebased': "yes",
        'option_conditions_irreversible': False,
    }

    try:
        spec = token_lib.CurrencySpec(currency_spec_dict)
    except TypeError:
        spec = 32

    assert spec == 32

    currency_spec_dict = {
        'name': name,
        'symbol': symbol,
        'option_witnesses_required': True,
        'option_expiration_rebased': True,
        'option_conditions_irreversible': "no",
    }

    try:
        spec = token_lib.CurrencySpec(currency_spec_dict)
    except TypeError:
        spec = 33

    assert spec == 33


def test_condition_asset_body():

    condition = 30
    body = token_lib.ConditionAssetBody(condition)

    dat = body.serialize()
    idx, body = token_lib.ConditionAssetBody.from_serialized_data(0, dat)

    assert idx == 1
    assert body.condition == condition


def test_store():

    mint_id, keypairs = idPubkeyMap.create_user_id(num_pubkeys=1)

    #app = bbc_app.BBcAppClient(port=DEFAULT_CORE_PORT, loglevel="all")
    app = bbc_app.BBcAppClient(port=DEFAULT_CORE_PORT, multiq=False, loglevel="all")
    app.set_user_id(mint_id)
    app.set_domain_id(domain_id)
    app.set_callback(bbc_app.Callback())
    ret = app.register_to_core()

    store = token_lib.Store(domain_id, mint_id, app)

    currency_spec = token_lib.CurrencySpec({
        'name': "Japanese Yen",
        'symbol': "JPY",
    })

    store.set_condition(0, keypair=keypairs[0], idPublickeyMap=idPubkeyMap)
    store.set_currency_spec(currency_spec, keypair=keypairs[0],
            idPublickeyMap=idPubkeyMap)

    assert store.get_condition() == 0
    assert store.get_currency_spec() == currency_spec

    assert store.store_ids[0] != store.store_ids[1]


def test_mint():

    currency_spec = token_lib.CurrencySpec({
        'name': "BBc Point",
        'symbol': "BBP",
    })

    mint = token_lib.BBcMint(domain_id, mint_id, mint_id, idPubkeyMap)
    mint.set_condition(0, keypair=keypairs[0])
    mint.set_currency_spec(currency_spec, keypair=keypairs[0])

    assert mint.get_condition() == 0
    assert mint.get_currency_spec() == currency_spec

    user_a_id, keypairs_a = idPubkeyMap.create_user_id(num_pubkeys=1)
    user_b_id, keypairs_b = idPubkeyMap.create_user_id(num_pubkeys=1)

    mint.issue(user_a_id, 1000, keypair=keypairs[0])

    assert mint.get_balance_of(user_a_id) == 1000
    assert mint.get_balance_of(user_b_id) == 0

    mint.transfer(user_a_id, user_b_id, 100,
                    keypair_from=keypairs_a[0], keypair_mint=keypairs[0])

    assert mint.get_balance_of(user_a_id) == 900
    assert mint.get_balance_of(user_b_id) == 100

    mint.issue(user_a_id, 10, keypair=keypairs[0])

    assert mint.get_balance_of(user_a_id) == 910
    assert mint.get_balance_of(user_b_id) == 100

    mint.transfer(user_a_id, user_b_id, 100,
                    keypair_from=keypairs_a[0], keypair_mint=keypairs[0])

    assert mint.get_balance_of(user_a_id) == 810
    assert mint.get_balance_of(user_b_id) == 200


def test_mint_depreciation():

    currency_spec = token_lib.CurrencySpec({
        'name': 'BBc X',
        'symbol': 'BBX',
        'decimal': 2,
        'variation_specs': [
            {
                'condition': 0,
                'variation_type': "simple",
                'rate': "-1/100",
                'rate_to_stop': 0,
                'time_unit': 4,
                'expire_after': 0,
            }
        ],
    })

    mint = token_lib.BBcMint(domain_id, mint_id, mint_id, idPubkeyMap)
    mint.set_condition(0, keypair=keypairs[0])
    mint.set_currency_spec(currency_spec, keypair=keypairs[0])

    assert mint.get_condition() == 0
    assert mint.get_currency_spec() == currency_spec

    user_a_id, keypairs_a = idPubkeyMap.create_user_id(num_pubkeys=1)
    user_b_id, keypairs_b = idPubkeyMap.create_user_id(num_pubkeys=1)

    mint.issue(user_a_id, 100000, keypair=keypairs[0])

    assert mint.get_balance_of(user_a_id) == 100000
    assert mint.get_balance_of(user_b_id) == 0

    print("\n5-second interval.")
    time.sleep(5)

    assert mint.get_balance_of(user_a_id) == 99000
    assert mint.get_balance_of(user_b_id) == 0

    mint.transfer(user_a_id, user_b_id, 10000,
                    keypair_from=keypairs_a[0], keypair_mint=keypairs[0])

    assert mint.get_balance_of(user_a_id) == 88999
    assert mint.get_balance_of(user_b_id) == 10000

    mint.issue(user_a_id, 1000, keypair=keypairs[0])

    assert mint.get_balance_of(user_a_id) == 89999
    assert mint.get_balance_of(user_b_id) == 10000

    mint.transfer(user_a_id, user_b_id, 10000,
                    keypair_from=keypairs_a[0], keypair_mint=keypairs[0])

    assert mint.get_balance_of(user_a_id) == 79998
    assert mint.get_balance_of(user_b_id) == 20000


def test_mint_sign_requested():

    currency_spec = token_lib.CurrencySpec({
        'name': "BBc Point",
        'symbol': "BBP",
    })

    mint = token_lib.BBcMint(domain_id, mint_id, mint_id, idPubkeyMap)
    mint.set_condition(0, keypair=keypairs[0])
    mint.set_currency_spec(currency_spec, keypair=keypairs[0])

    assert mint.get_condition() == 0
    assert mint.get_currency_spec() == currency_spec

    user_a_id, keypairs_a = idPubkeyMap.create_user_id(num_pubkeys=1)
    user_b_id, keypairs_b = idPubkeyMap.create_user_id(num_pubkeys=1)

    mint_a = token_lib.BBcMint(domain_id, mint_id, user_a_id, idPubkeyMap)

    mint.set_keypair(keypairs[0])

    mint.issue(user_a_id, 1000, keypair=keypairs[0])

    assert mint.get_balance_of(user_a_id) == 1000
    assert mint.get_balance_of(user_b_id) == 0

    mint_a.transfer(user_a_id, user_b_id, 100,
                    keypair_from=keypairs_a[0])

    assert mint.get_balance_of(user_a_id) == 900
    assert mint.get_balance_of(user_b_id) == 100

    mint.issue(user_a_id, 10, keypair=keypairs[0])

    assert mint.get_balance_of(user_a_id) == 910
    assert mint.get_balance_of(user_b_id) == 100

    mint_a.transfer(user_a_id, user_b_id, 100,
                    keypair_from=keypairs_a[0])

    assert mint.get_balance_of(user_a_id) == 810
    assert mint.get_balance_of(user_b_id) == 200


def test_swap():

    currency_spec = token_lib.CurrencySpec({
        'name': "BBc Point",
        'symbol': "BBP",
    })

    currency_spec_counter = token_lib.CurrencySpec({
        'name': "BBX Point",
        'symbol': "BBX",
    })

    mint = token_lib.BBcMint(domain_id, mint_id, mint_id, idPubkeyMap)

    label_group_id = bbclib.get_new_id('label_group', include_timestamp=False)
    label_id = TransactionLabel.create_label_id('label1', '3')
    label = TransactionLabel(label_group_id, label_id=label_id)

    tx = mint.set_condition(0, keypair=keypairs[0], label=label)

    assert label.get_label_id(tx) == label_id

    label.label_id = TransactionLabel.create_label_id('label2', '3')

    tx = mint.set_currency_spec(currency_spec, keypair=keypairs[0],
            label=label)

    assert label.is_labeled(tx)

    counter_mint = token_lib.BBcMint(domain_id, mint_id_counter,
            mint_id_counter, idPubkeyMap)
    counter_mint.set_condition(0, keypair=keypairs_counter[0])
    counter_mint.set_currency_spec(currency_spec_counter,
            keypair=keypairs_counter[0])

    user_a_id, keypairs_a = idPubkeyMap.create_user_id(num_pubkeys=1)
    user_b_id, keypairs_b = idPubkeyMap.create_user_id(num_pubkeys=1)

    label.label_id = TransactionLabel.create_label_id('label3', '3')

    tx = mint.issue(user_a_id, 1000, keypair=keypairs[0], label=label)

    assert label.is_labeled(tx)

    counter_mint.issue(user_b_id, 3000, keypair=keypairs_counter[0])

    assert mint.get_balance_of(user_a_id) == 1000
    assert counter_mint.get_balance_of(user_b_id) == 3000

    label.label_id = TransactionLabel.create_label_id('label4', '3')

    tx = mint.swap(counter_mint, user_a_id, user_b_id, 100, 300,
                    keypair_this=keypairs_a[0], keypair_that=keypairs_b[0],
                    keypair_mint=keypairs[0],
                    keypair_counter_mint=keypairs_counter[0], label=label)

    assert label.is_labeled(tx)

    assert mint.get_balance_of(user_a_id) == 900
    assert mint.get_balance_of(user_b_id) == 100
    assert counter_mint.get_balance_of(user_a_id) == 300
    assert counter_mint.get_balance_of(user_b_id) == 2700

    mint.issue(user_a_id, 10, keypair=keypairs[0])

    assert mint.get_balance_of(user_a_id) == 910
    assert mint.get_balance_of(user_b_id) == 100

    label.label_id = TransactionLabel.create_label_id('label5', '3')

    tx = mint.transfer(user_a_id, user_b_id, 100,
            keypair_from=keypairs_a[0], keypair_mint=keypairs[0],
            label=label)

    assert label.is_labeled(tx)

    label.label_id = TransactionLabel.create_label_id('label6', '3')

    assert label.is_labeled(tx) == False

    assert mint.get_balance_of(user_a_id) == 810
    assert mint.get_balance_of(user_b_id) == 200

    counter_mint.issue(user_a_id, 10, keypair=keypairs_counter[0])

    assert counter_mint.get_balance_of(user_a_id) == 310
    assert counter_mint.get_balance_of(user_b_id) == 2700

    counter_mint.transfer(user_a_id, user_b_id, 100,
                    keypair_from=keypairs_a[0],
                    keypair_mint=keypairs_counter[0])

    assert counter_mint.get_balance_of(user_a_id) == 210
    assert counter_mint.get_balance_of(user_b_id) == 2800

    mint.close()
    counter_mint.close()


# end of tests/test_token_lib.py
