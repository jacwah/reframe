# Copyright 2016-2022 Swiss National Supercomputing Centre (CSCS/ETH Zurich)
# ReFrame Project Developers. See the top-level LICENSE file for details.
#
# SPDX-License-Identifier: BSD-3-Clause

import pytest

import reframe as rfm
import reframe.core.exceptions as errors
import reframe.frontend.executors as executors
import reframe.frontend.filters as filters
import reframe.utility.sanity as sn
import unittests.utility as test_util


def count_checks(filter_fn, checks):
    return sn.count(filter(filter_fn, checks))


def make_case(*args, **kwargs):
    test = test_util.make_check(*args, **kwargs)
    return executors.TestCase(test, None, None)


@pytest.fixture
def sample_cases():
    class _X(rfm.RegressionTest):
        valid_systems = ['*']
        valid_prog_environs = ['*']

    return [
        make_case(_X, alt_name='check1',
                  tags={'a', 'b', 'c', 'd'},
                  num_gpus_per_node=1,
                  maintainers=['A', 'B', 'C', 'D']),
        make_case(_X, alt_name='check2',
                  tags={'x', 'y', 'z'},
                  num_gpus_per_node=0,
                  maintainers=['X', 'Y', 'Z']),
        make_case(_X, alt_name='check3',
                  tags={'a', 'z'},
                  num_gpus_per_node=1,
                  maintainers=['A', 'Z'])
    ]


@pytest.fixture
def use_compact_names(make_exec_ctx_g):
    yield from make_exec_ctx_g(options={'general/compact_test_names': True})


@pytest.fixture
def sample_param_cases(use_compact_names):
    class _X(rfm.RegressionTest):
        p = parameter([1, 1, 3])
        valid_systems = ['*']
        valid_prog_environs = ['*']

    return [executors.TestCase(_X(variant_num=v), None, None)
            for v in range(_X.num_variants)]


@pytest.fixture
def sample_param_cases_compat():
    # Param cases with the old naming scheme; i.e., with
    # `general/compact_test_names=False`

    class _X(rfm.RegressionTest):
        p = parameter([1, 1, 3])
        valid_systems = ['*']
        valid_prog_environs = ['*']

    return [executors.TestCase(_X(variant_num=v), None, None)
            for v in range(_X.num_variants)]


def test_have_name(sample_cases):
    assert 1 == count_checks(filters.have_name('check1'), sample_cases)
    assert 3 == count_checks(filters.have_name('check'), sample_cases)
    assert 2 == count_checks(filters.have_name(r'\S*1|\S*3'), sample_cases)
    assert 0 == count_checks(filters.have_name('Check'), sample_cases)
    assert 3 == count_checks(filters.have_name('(?i)Check'), sample_cases)
    assert 2 == count_checks(filters.have_name('(?i)check1|CHECK2'),
                             sample_cases)


def test_have_name_param_test(sample_param_cases):
    assert 2 == count_checks(filters.have_name('.*%p=1'), sample_param_cases)
    assert 1 == count_checks(filters.have_name('_X%p=3'), sample_param_cases)
    assert 1 == count_checks(filters.have_name('_X@2'), sample_param_cases)


def test_have_name_param_test_compat(sample_param_cases_compat):
    assert 0 == count_checks(filters.have_name('.*%p=1'),
                             sample_param_cases_compat)
    assert 0 == count_checks(filters.have_name('_X%p=3'),
                             sample_param_cases_compat)
    assert 0 == count_checks(filters.have_name('_X@2'),
                             sample_param_cases_compat)
    assert 2 == count_checks(filters.have_name('_X_1'),
                             sample_param_cases_compat)


def test_have_not_name(sample_cases):
    assert 2 == count_checks(filters.have_not_name('check1'), sample_cases)
    assert 1 == count_checks(filters.have_not_name('check1|check3'),
                             sample_cases)
    assert 0 == count_checks(filters.have_not_name('check1|check2|check3'),
                             sample_cases)
    assert 3 == count_checks(filters.have_not_name('Check1'), sample_cases)
    assert 2 == count_checks(filters.have_not_name('(?i)Check1'),
                             sample_cases)


def test_have_tags(sample_cases):
    assert 2 == count_checks(filters.have_tag('a|c'), sample_cases)
    assert 0 == count_checks(filters.have_tag('p|q'), sample_cases)
    assert 2 == count_checks(filters.have_tag('z'), sample_cases)


def test_have_not_tags(sample_cases):
    assert 1 == count_checks(filters.have_not_tag('a|c'), sample_cases)
    assert 3 == count_checks(filters.have_not_tag('p|q'), sample_cases)
    assert 1 == count_checks(filters.have_not_tag('z'), sample_cases)


def test_have_maintainers(sample_cases):
    assert 2 == count_checks(filters.have_maintainer('A|C'), sample_cases)
    assert 0 == count_checks(filters.have_maintainer('P|Q'), sample_cases)
    assert 2 == count_checks(filters.have_maintainer('Z'), sample_cases)


def test_have_gpu_only(sample_cases):
    assert 2 == count_checks(filters.have_gpu_only(), sample_cases)


def test_have_cpu_only(sample_cases):
    assert 1 == count_checks(filters.have_cpu_only(), sample_cases)


def test_invalid_regex(sample_cases):
    # We need to explicitly call `evaluate` to make sure the exception
    # is triggered in all cases
    with pytest.raises(errors.ReframeError):
        count_checks(filters.have_name('*foo'), sample_cases).evaluate()

    with pytest.raises(errors.ReframeError):
        count_checks(filters.have_not_name('*foo'), sample_cases).evaluate()

    with pytest.raises(errors.ReframeError):
        count_checks(filters.have_tag('*foo'), sample_cases).evaluate()
