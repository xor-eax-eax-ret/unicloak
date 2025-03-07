from libcst.metadata import (
    QualifiedNameProvider,
    QualifiedNameSource,
    ScopeProvider,
    ClassScope,
    FunctionScope,
    TypeInferenceProvider,
    ParentNodeProvider
)
import libcst as cst
import random 
from typing import Optional
from yaspin.spinners import Spinners
from yaspin import kbi_safe_yaspin
import builtins


class RandomizeAttributes(cst.CSTTransformer):
    """
    Replaces class methods and attributes with a randomized string.
    Only does so for user-defined classes.
    """

    METADATA_DEPENDENCIES = (
        QualifiedNameProvider,
        ScopeProvider,
        TypeInferenceProvider,
        ParentNodeProvider
    )

    def __init__(self):
        self.randomize_map = {}
        self.avoid_names = ["self", "__init__", "main", "super"]
        self.avoid_names.extend(dir(builtins))
        self.ignore = False
        self.first_visit = True
        self.progress_msg = "Randomizing methods and attributes..."
        self.spinner = None

        class DummyClass:
            pass
            
        def dummyFunc():
            pass
        types_to_inspect = [
            object,
            int,
            float,
            str,
            list,
            dict,
            set,
            tuple,
            DummyClass,
            dummyFunc,
            # Avoid messing with the lambda strings which use
            # __code__ as well 
            dummyFunc.__code__
        ]
        for t in types_to_inspect:
            self.avoid_names.extend(method for method in dir(t))

    def rand_name(self):
        keys = [
            "I",
            "l",
            "i",
            "Î",
            "Ĳ",
            "ĳ",
            "ǉ",
            "Ḭ",
            "j",
            "J",
            "Ĵ",
            "ⅉ",
            "ｊ"
        ]
        return ''.join(random.choices(keys, k=8))
    
    def visit_Node(self, node):
        if self.first_visit is True:
            self.spinner = kbi_safe_yaspin(
                Spinners.simpleDotsScrolling,
                text=self.progress_msg,
                timer=True
            )
            self.spinner.start()
            self.first_visit = False

    def leave_Attribute(
        self,
        original_node: cst.Attribute,
        updated_node: cst.Attribute
    ) -> Optional[bool]:
        try:
            scope = self.get_metadata(ScopeProvider, original_node)
        except KeyError:
            return updated_node
        qualified_names = list(scope.get_qualified_names_for(original_node))
        if not qualified_names:
            return updated_node
        qualified_name = qualified_names[0]
        if isinstance(scope, FunctionScope):
            if qualified_name.source == QualifiedNameSource.LOCAL:
                if original_node.attr.value not in self.avoid_names:
                    if original_node.attr.value not in self.randomize_map:
                        new_name = self.rand_name()
                        self.randomize_map[original_node.attr.value] = new_name
                        return updated_node.with_changes(
                            attr=cst.Name(
                                value=new_name
                            )
                        )
                    else:
                        return updated_node.with_changes(
                            attr=cst.Name(
                                value=self.randomize_map[original_node.attr.value]
                            )
                        ) 
                else:
                    return updated_node
            else:
                return updated_node
        else:
            # The user didn't define this attribute, so leave it unchanged so 
            # we don't break anything
            if original_node.attr.value not in self.randomize_map:
                return updated_node
            else:
                return updated_node.with_changes(
                    attr=cst.Name(
                        value=self.randomize_map[original_node.attr.value]
                    )
                )

    def leave_FunctionDef(
        self,
        original_node: cst.FunctionDef,
        updated_node: cst.FunctionDef
    ):
        # Only target methods as RandomizeNames skips them
        scope = self.get_metadata(ScopeProvider, original_node)
        if isinstance(scope, ClassScope):
            if original_node.name.value not in self.avoid_names:
                if original_node.name.value in self.randomize_map:
                    new_value = self.randomize_map[original_node.name.value]
                else:
                    new_value = self.rand_name()
                    self.randomize_map[original_node.name.value] = new_value
                return updated_node.with_changes(
                    name=cst.Name(
                        value=str(new_value)
                    )
                )
            else:
                return updated_node
        else:
            return updated_node