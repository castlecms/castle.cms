import unittest

import robotsuite
from castle.cms.testing import CASTLE_ROBOT_TESTING
from plone.testing import layered


def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([
        layered(robotsuite.RobotTestSuite("robot/test_hello.robot"),
                layer=CASTLE_ROBOT_TESTING),
    ])
    return suite
