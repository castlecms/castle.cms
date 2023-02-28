import os
import unittest

import robotsuite
from plone.testing import layered

from castle.cms.testing import CASTLE_ROBOT_TESTING


dir_path = os.path.dirname(os.path.realpath(__file__))


def test_suite():
    suite = unittest.TestSuite()

    for filename in os.listdir(os.path.join(dir_path, 'robot')):
        if (not filename.startswith('test_') or
                not filename.endswith('.robot')):
            continue
        filepath = os.path.join('robot', filename)
        suite.addTests([
            layered(robotsuite.RobotTestSuite(filepath),
                    layer=CASTLE_ROBOT_TESTING),
        ])
    return suite
