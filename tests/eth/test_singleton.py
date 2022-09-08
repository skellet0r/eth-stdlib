from collections import UserList

from eth.singleton import Singleton, SingletonABC


def test_class_call_returns_same_instance():
    assert Singleton() is Singleton()
    assert Singleton().__class__ is Singleton


def test_derived_class_call_returns_same_instance():
    class Foo(Singleton):
        pass

    assert Foo() is Foo()
    assert Foo().__class__ is Foo
    assert Foo() is not Singleton()


def test_creating_singleton_abc_with_mixin():
    class Foo(SingletonABC, UserList):
        pass

    assert Foo() is Foo()
    assert Foo().__class__ is Foo
    assert Foo() is not SingletonABC()
