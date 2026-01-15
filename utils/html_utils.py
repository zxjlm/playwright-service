#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author: harumonia
@Email: zxjlm233@gmail.net
@Create Time: 2026-01-15 15:05:07
@Software: Visual Studio Code
@Copyright: Copyright (c) 2026, harumonia
@Description: ...
All Rights Reserved.
"""


def count_leaf_nodes(doc):
    """Count the number of leaf nodes in a JustHTML document.

    A leaf node is any node with no children (text nodes, comments,
    or elements without child elements).
    """

    def count_leaves(node):
        # If node has no children, it's a leaf
        if not node.has_child_nodes():
            return 1

        # Otherwise, count leaves in all children
        count = 0
        for child in node.children:
            count += count_leaves(child)
        return count

    return count_leaves(doc.root)
