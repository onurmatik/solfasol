(function () {
  const calculator = document.querySelector("[data-payment-calculator]");
  if (!calculator) {
    return;
  }

  const quantityInput = calculator.querySelector("[data-payment-quantity]");
  const totalOutput = calculator.querySelector("[data-payment-total]");
  const unitPrice = Number.parseInt(calculator.dataset.unitPrice, 10);
  const formatter = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 0 });

  if (!quantityInput || !totalOutput || Number.isNaN(unitPrice)) {
    return;
  }

  function updatePaymentTotal() {
    const quantity = Number.parseInt(quantityInput.value, 10);
    const total = Number.isFinite(quantity) && quantity > 0 ? quantity * unitPrice : 0;
    totalOutput.textContent = formatter.format(total);
  }

  quantityInput.addEventListener("input", updatePaymentTotal);
  updatePaymentTotal();
})();
