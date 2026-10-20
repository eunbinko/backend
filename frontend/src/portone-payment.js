import * as PortOne from '@portone/browser-sdk/v2'

export function requestReportPayment(order, redirectUrl = window.location.href) {
  return PortOne.requestPayment({
    storeId: order.store_id,
    channelKey: order.channel_key,
    paymentId: order.payment_id,
    orderName: order.order_name,
    totalAmount: order.amount_krw,
    currency: 'CURRENCY_KRW',
    payMethod: 'CARD',
    redirectUrl,
    forceRedirect: true,
  })
}
