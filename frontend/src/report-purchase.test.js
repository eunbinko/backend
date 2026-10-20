import { requestReportPayment } from './portone-payment'
import * as PortOne from '@portone/browser-sdk/v2'

jest.mock('@portone/browser-sdk/v2', () => ({ requestPayment: jest.fn() }))

describe('PortOne V2 report payment', () => {
  beforeEach(() => PortOne.requestPayment.mockReset())
  test('uses server-created order parameters and mobile redirect mode', async () => {
    const order = { store_id: 'store-x', channel_key: 'channel-y', payment_id: 'order-z', order_name: 'ESG report', amount_krw: 2000 }
    PortOne.requestPayment.mockResolvedValue({ paymentId: 'order-z' })
    await requestReportPayment(order, 'https://site.test/reports/9')
    expect(PortOne.requestPayment).toHaveBeenCalledWith({
      storeId: 'store-x', channelKey: 'channel-y', paymentId: 'order-z', orderName: 'ESG report',
      totalAmount: 2000, currency: 'CURRENCY_KRW', payMethod: 'CARD',
      redirectUrl: 'https://site.test/reports/9', forceRedirect: true,
    })
  })
})
