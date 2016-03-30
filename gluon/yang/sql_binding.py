#!/usr/bin/env python
"""
Author Naveen Joy najoy@cisco.com
Parses an input yang module and generates SQLAlchemy Model objects
"""
import os
import pyangbind

YANGMODULE="gluon-port"


def generate_python_bindings():
    """
    Generates Yang to python bindings for the yangmodule named binding.py
    returns: the python binding module object name
    rtype: string
    """
    this_dir = os.path.dirname(os.path.realpath(__file__))
    pyang_plugin = "%s/plugin" % os.path.dirname(pyangbind.__file__)
    binding_name = "binding.py" % YANGMODULE
    binding_path = "%s/%s" % (this_dir, binding_name)
    cmd = "%s " % "pyang"
    cmd += "--plugindir %s" % pyang_plugin
    cmd += " -f pybind -o %s" % binding_path
    cmd += " -p %s" % this_dir
    cmd += " %s/%s.yang" % (this_dir, YANGMODULE)
    print(cmd)
    os.system(cmd)
    return binding_path



if __name__ == "__main__":
    generate_python_bindings()

