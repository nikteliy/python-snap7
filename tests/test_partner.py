import logging
import pytest
import unittest as unittest
from unittest import mock

import snap7.partner

logging.basicConfig(level=logging.WARNING)


@pytest.mark.partner
class TestPartner(unittest.TestCase):
    def setUp(self) -> None:
        self.partner = snap7.partner.Partner()
        self.partner.start()

    def tearDown(self) -> None:
        self.partner.stop()
        self.partner.destroy()

    def test_as_b_send(self) -> None:
        self.partner.as_b_send()

    @unittest.skip("we don't recv something yet")
    def test_b_recv(self) -> None:
        self.partner.b_recv()

    def test_b_send(self) -> None:
        self.partner.b_send()

    def test_check_as_b_recv_completion(self) -> None:
        self.partner.check_as_b_recv_completion()

    def test_check_as_b_send_completion(self) -> None:
        self.partner.check_as_b_send_completion()

    def test_create(self) -> None:
        self.partner.create()

    def test_destroy(self) -> None:
        self.partner.destroy()

    def test_error_text(self) -> None:
        snap7.common.error_text(0, context="partner")

    def test_get_last_error(self) -> None:
        self.partner.get_last_error()

    def test_get_param(self) -> None:
        expected = (
            (snap7.types.LocalPort, 0),
            (snap7.types.RemotePort, 102),
            (snap7.types.PingTimeout, 750),
            (snap7.types.SendTimeout, 10),
            (snap7.types.RecvTimeout, 3000),
            (snap7.types.SrcRef, 256),
            (snap7.types.DstRef, 0),
            (snap7.types.PDURequest, 480),
            (snap7.types.WorkInterval, 100),
            (snap7.types.BSendTimeout, 3000),
            (snap7.types.BRecvTimeout, 3000),
            (snap7.types.RecoveryTime, 500),
            (snap7.types.KeepAliveTime, 5000),
        )
        for param, value in expected:
            self.assertEqual(self.partner.get_param(param), value)

        self.assertRaises(Exception, self.partner.get_param, snap7.types.MaxClients)

    def test_get_stats(self) -> None:
        self.partner.get_stats()

    def test_get_status(self) -> None:
        self.partner.get_status()

    def test_get_times(self) -> None:
        self.partner.get_times()

    def test_set_param(self) -> None:
        values = (
            (snap7.types.PingTimeout, 800),
            (snap7.types.SendTimeout, 15),
            (snap7.types.RecvTimeout, 3500),
            (snap7.types.WorkInterval, 50),
            (snap7.types.SrcRef, 128),
            (snap7.types.DstRef, 128),
            (snap7.types.SrcTSap, 128),
            (snap7.types.PDURequest, 470),
            (snap7.types.BSendTimeout, 2000),
            (snap7.types.BRecvTimeout, 2000),
            (snap7.types.RecoveryTime, 400),
            (snap7.types.KeepAliveTime, 4000),
        )
        for param, value in values:
            self.partner.set_param(param, value)

        self.assertRaises(Exception, self.partner.set_param, snap7.types.RemotePort, 1)

    def test_set_recv_callback(self) -> None:
        self.partner.set_recv_callback()

    def test_set_send_callback(self) -> None:
        self.partner.set_send_callback()

    def test_start(self) -> None:
        self.partner.start()

    def test_start_to(self) -> None:
        self.partner.start_to("0.0.0.0", "0.0.0.0", 0, 0)  # noqa: S104

    def test_stop(self) -> None:
        self.partner.stop()

    def test_wait_as_b_send_completion(self) -> None:
        self.assertRaises(RuntimeError, self.partner.wait_as_b_send_completion)


@pytest.mark.partner
class TestLibraryIntegration(unittest.TestCase):
    def setUp(self) -> None:
        # replace the function load_library with a mock
        self.loadlib_patch = mock.patch("snap7.partner.load_library")
        self.loadlib_func = self.loadlib_patch.start()

        # have load_library return another mock
        self.mocklib = mock.MagicMock()
        self.loadlib_func.return_value = self.mocklib

        # have the Par_Create of the mock return None
        self.mocklib.Par_Create.return_value = None

    def tearDown(self) -> None:
        # restore load_library
        self.loadlib_patch.stop()

    def test_create(self) -> None:
        snap7.partner.Partner()
        self.mocklib.Par_Create.assert_called_once()

    def test_gc(self) -> None:
        partner = snap7.partner.Partner()
        del partner
        self.mocklib.Par_Destroy.assert_called_once()


if __name__ == "__main__":
    unittest.main()
