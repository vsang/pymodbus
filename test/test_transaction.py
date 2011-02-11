import unittest
from binascii import a2b_hex
from pymodbus.pdu import *
from pymodbus.transaction import *
from pymodbus.factory import ServerDecoder

class SimpleDataStoreTest(unittest.TestCase):
    '''
    This is the unittest for the pymod.transaction module
    '''

    #---------------------------------------------------------------------------# 
    # Test Construction
    #---------------------------------------------------------------------------# 
    def setUp(self):
        ''' Sets up the test environment '''
        self.decoder  = ServerDecoder()
        self._manager = ModbusTransactionManager()
        self._tcp     = ModbusSocketFramer(decoder=self.decoder)
        self._rtu     = ModbusRtuFramer(decoder=self.decoder)
        self._ascii   = ModbusAsciiFramer(decoder=self.decoder)
        self._binary  = ModbusBinaryFramer(decoder=self.decoder)

    def tearDown(self):
        ''' Cleans up the test environment '''
        del self._manager    
        del self._tcp        
        del self._rtu        
        del self._ascii      

    #---------------------------------------------------------------------------# 
    # Other Class tests
    #---------------------------------------------------------------------------# 
    def testModbusTransactionManagerTID(self):
        ''' Test the tcp transaction manager TID '''
        self.assertEqual(id(self._manager), id(ModbusTransactionManager()))
        for i in range(10):
            self.assertEqual(i+1, self._manager.getNextTID())
        self._manager.resetTID()
        self.assertEqual(1, self._manager.getNextTID())

    def testModbusTransactionManagerTransaction(self):
        ''' Test the tcp transaction manager '''
        class Request:
            pass
        self._manager.resetTID()
        handle = Request()
        handle.transaction_id = self._manager.getNextTID()
        handle.message = "testing"

        self._manager.addTransaction(handle)
        result = self._manager.getTransaction(handle.transaction_id)
        self.assertEqual(handle.message, result.message)
        self._manager.delTransaction(handle.transaction_id)
        self.assertEqual(None, self._manager.getTransaction(handle.transaction_id))

    #---------------------------------------------------------------------------# 
    # TCP tests
    #---------------------------------------------------------------------------# 
    def testTCPFramerTransactionReady(self):
        ''' Test a tcp frame transaction '''
        msg = "\x00\x01\x12\x34\x00\x04\xff\x02\x12\x34"
        self.assertFalse(self._tcp.isFrameReady())
        self.assertFalse(self._tcp.checkFrame())
        self._tcp.addToFrame(msg)
        self.assertTrue(self._tcp.isFrameReady())
        self.assertTrue(self._tcp.checkFrame())
        self._tcp.advanceFrame()
        self.assertFalse(self._tcp.isFrameReady())
        self.assertFalse(self._tcp.checkFrame())
        self.assertEqual('', self._ascii.getFrame())

    def testTCPFramerTransactionFull(self):
        ''' Test a full tcp frame transaction '''
        msg = "\x00\x01\x12\x34\x00\x04\xff\x02\x12\x34"
        self._tcp.addToFrame(msg)
        self.assertTrue(self._tcp.checkFrame())
        result = self._tcp.getFrame()
        self.assertEqual(msg[7:], result)
        self._tcp.advanceFrame()

    def testTCPFramerTransactionHalf(self):
        ''' Test a half completed tcp frame transaction '''
        msg1 = "\x00\x01\x12\x34\x00"
        msg2 = "\x04\xff\x02\x12\x34"
        self._tcp.addToFrame(msg1)
        self.assertFalse(self._tcp.checkFrame())
        result = self._tcp.getFrame()
        self.assertEqual('', result)
        self._tcp.addToFrame(msg2)
        self.assertTrue(self._tcp.checkFrame())
        result = self._tcp.getFrame()
        self.assertEqual(msg2[2:], result)
        self._tcp.advanceFrame()

    def testTCPFramerTransactionHalf2(self):
        ''' Test a half completed tcp frame transaction '''
        msg1 = "\x00\x01\x12\x34\x00\x04\xff"
        msg2 = "\x02\x12\x34"
        self._tcp.addToFrame(msg1)
        self.assertFalse(self._tcp.checkFrame())
        result = self._tcp.getFrame()
        self.assertEqual('', result)
        self._tcp.addToFrame(msg2)
        self.assertTrue(self._tcp.checkFrame())
        result = self._tcp.getFrame()
        self.assertEqual(msg2, result)
        self._tcp.advanceFrame()

    def testTCPFramerTransactionShort(self):
        ''' Test that we can get back on track after an invalid message '''
        msg1 = "\x99\x99\x99\x99\x00\x01\x00\x01"
        msg2 = "\x00\x01\x12\x34\x00\x05\xff\x02\x12\x34"
        self._tcp.addToFrame(msg1)
        self.assertFalse(self._tcp.checkFrame())
        result = self._tcp.getFrame()
        self.assertEqual('', result)
        self._tcp.advanceFrame()
        self._tcp.addToFrame(msg2)
        self.assertEqual(10, len(self._tcp._ModbusSocketFramer__buffer))
        self.assertTrue(self._tcp.checkFrame())
        result = self._tcp.getFrame()
        self.assertEqual(msg2[7:], result)
        self._tcp.advanceFrame()

    def testTCPFramerPopulate(self):
        ''' Test a tcp frame packet build '''
        expected = ModbusRequest()
        expected.transaction_id = 0x0001
        expected.protocol_id    = 0x1234
        expected.unit_id        = 0xff
        msg = "\x00\x01\x12\x34\x00\x04\xff\x02\x12\x34"
        self._tcp.addToFrame(msg)
        self.assertTrue(self._tcp.checkFrame())
        actual = ModbusRequest()
        self._tcp.populateResult(actual)
        for name in ['transaction_id', 'protocol_id', 'unit_id']:
            self.assertEqual(getattr(expected, name), getattr(actual, name))
        self._tcp.advanceFrame()

    def testTCPFramerPacket(self):
        ''' Test a tcp frame packet build '''
        old_encode = ModbusRequest.encode
        ModbusRequest.encode = lambda self: ''
        message = ModbusRequest()
        message.transaction_id = 0x0001
        message.protocol_id    = 0x1234
        message.unit_id        = 0xff
        message.function_code  = 0x01
        expected = "\x00\x01\x12\x34\x00\x02\xff\x01"
        actual = self._tcp.buildPacket(message)
        self.assertEqual(expected, actual)
        ModbusRequest.encode = old_encode

    #---------------------------------------------------------------------------# 
    # RTU tests
    #---------------------------------------------------------------------------# 
    def testRTUFramerTransactionReady(self):
        ''' Test a rtu frame transaction '''
        msg = ":\xab\xcd\x12\x34\x12\x34\xaa\xaa\r\n"
        self.assertFalse(self._rtu.isFrameReady())
        self.assertFalse(self._rtu.checkFrame())
        # test a full transaction

    def testRTUFramerTransactionFull(self):
        ''' Test a full rtu frame transaction '''
        pass

    def testRTUFramerTransactionHalf(self):
        ''' Test a half completed rtu frame transaction '''
        pass

    def testRTUFramerPopulate(self):
        ''' Test a rtu frame packet build '''
        request = ModbusRequest()
        self._rtu.populateResult(request)
        self.assertEqual(0x00, request.unit_id)

    def testRTUFramerPacket(self):
        ''' Test a rtu frame packet build '''
        pass

    #---------------------------------------------------------------------------# 
    # ASCII tests
    #---------------------------------------------------------------------------# 
    def testASCIIFramerTransactionReady(self):
        ''' Test a ascii frame transaction '''
        msg = ":abcd12341234aae6\r\n"
        self.assertFalse(self._ascii.isFrameReady())
        self.assertFalse(self._ascii.checkFrame())
        self._ascii.addToFrame(msg)
        self.assertTrue(self._ascii.isFrameReady())
        self.assertTrue(self._ascii.checkFrame())
        self._ascii.advanceFrame()
        self.assertFalse(self._ascii.isFrameReady())
        self.assertFalse(self._ascii.checkFrame())
        self.assertEqual('', self._ascii.getFrame())

    def testASCIIFramerTransactionFull(self):
        ''' Test a full ascii frame transaction '''
        msg  ='sss:01030000000AF2\r\n'
        pack = a2b_hex(msg[6:-4])
        self._ascii.addToFrame(msg)
        self.assertTrue(self._ascii.checkFrame())
        result = self._ascii.getFrame()
        self.assertEqual(pack, result)
        self._ascii.advanceFrame()

    def testASCIIFramerTransactionHalf(self):
        ''' Test a half completed ascii frame transaction '''
        msg1 = "sss:abcd1234"
        msg2 = "1234aaaa\r\n"
        pack = a2b_hex(msg1[6:] + msg2[:-4])
        self._ascii.addToFrame(msg1)
        self.assertFalse(self._ascii.checkFrame())
        result = self._ascii.getFrame()
        self.assertEqual('', result)
        self._ascii.addToFrame(msg2)
        self.assertTrue(self._ascii.checkFrame())
        result = self._ascii.getFrame()
        self.assertEqual(pack, result)
        self._ascii.advanceFrame()

    def testASCIIFramerPopulate(self):
        ''' Test a ascii frame packet build '''
        request = ModbusRequest()
        self._ascii.populateResult(request)
        self.assertEqual(0x00, request.unit_id)

    def testASCIIFramerPacket(self):
        ''' Test a ascii frame packet build '''
        old_encode = ModbusRequest.encode
        ModbusRequest.encode = lambda self: ''
        message = ModbusRequest()
        message.unit_id        = 0xff
        message.function_code  = 0x01
        expected = ":FF0100\r\n"
        actual = self._ascii.buildPacket(message)
        self.assertEqual(expected, actual)
        ModbusRequest.encode = old_encode

    #---------------------------------------------------------------------------# 
    # Binary tests
    #---------------------------------------------------------------------------# 
    def testBinaryFramerTransactionReady(self):
        ''' Test a binary frame transaction '''
        msg  = '\x7b\x01\x03\x00\x00\x00\x05\x85\xc9\x7d'
        self.assertFalse(self._binary.isFrameReady())
        self.assertFalse(self._binary.checkFrame())
        self._binary.addToFrame(msg)
        self.assertTrue(self._binary.isFrameReady())
        self.assertTrue(self._binary.checkFrame())
        self._binary.advanceFrame()
        self.assertFalse(self._binary.isFrameReady())
        self.assertFalse(self._binary.checkFrame())
        self.assertEqual('', self._binary.getFrame())

    def testBinaryFramerTransactionFull(self):
        ''' Test a full binary frame transaction '''
        msg  = '\x7b\x01\x03\x00\x00\x00\x05\x85\xc9\x7d'
        pack = msg[3:-3]
        self._binary.addToFrame(msg)
        self.assertTrue(self._binary.checkFrame())
        result = self._binary.getFrame()
        self.assertEqual(pack, result)
        self._binary.advanceFrame()

    def testBinaryFramerTransactionHalf(self):
        ''' Test a half completed binary frame transaction '''
        msg1 = '\x7b\x01\x03\x00'
        msg2 = '\x00\x00\x05\x85\xc9\x7d'
        pack = msg1[3:] + msg2[:-3]
        self._binary.addToFrame(msg1)
        self.assertFalse(self._binary.checkFrame())
        result = self._binary.getFrame()
        self.assertEqual('', result)
        self._binary.addToFrame(msg2)
        self.assertTrue(self._binary.checkFrame())
        result = self._binary.getFrame()
        self.assertEqual(pack, result)
        self._binary.advanceFrame()

    def testBinaryFramerPopulate(self):
        ''' Test a binary frame packet build '''
        request = ModbusRequest()
        self._binary.populateResult(request)
        self.assertEqual(0x00, request.unit_id)

    def testBinaryFramerPacket(self):
        ''' Test a binary frame packet build '''
        old_encode = ModbusRequest.encode
        ModbusRequest.encode = lambda self: ''
        message = ModbusRequest()
        message.unit_id        = 0xff
        message.function_code  = 0x01
        expected = '\xff\x01\x81\x80'
        actual = self._binary.buildPacket(message)
        self.assertEqual(expected, actual)
        ModbusRequest.encode = old_encode

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
