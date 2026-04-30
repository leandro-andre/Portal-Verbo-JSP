(function () {
  function getLoadingLabel(button) {
    if (!button) {
      return "Processando...";
    }

    if (button.dataset.loading) {
      return button.dataset.loading;
    }

    var label = (button.textContent || "").trim().toLowerCase();

    if (label.indexOf("salvar") !== -1) return "Salvando...";
    if (label.indexOf("enviar") !== -1) return "Enviando...";
    if (label.indexOf("atualizar") !== -1) return "Atualizando...";
    if (label.indexOf("publicar") !== -1 || label.indexOf("despublicar") !== -1) return "Atualizando status...";
    if (label.indexOf("cancelar") !== -1) return "Cancelando...";
    if (label.indexOf("remover") !== -1 || label.indexOf("excluir") !== -1) return "Removendo...";
    if (label.indexOf("desativar") !== -1 || label.indexOf("reativar") !== -1) return "Atualizando...";
    if (label.indexOf("resolvido") !== -1 || label.indexOf("exibido") !== -1) return "Atualizando...";

    return "Processando...";
  }

  function setButtonLoading(button) {
    if (!button || button.dataset.loadingApplied === "true") {
      return;
    }

    button.dataset.loadingApplied = "true";
    button.dataset.originalHtml = button.innerHTML;
    button.classList.add("is-loading");
    button.disabled = true;
    button.setAttribute("aria-busy", "true");
    button.innerHTML =
      '<span class="btn__spinner" aria-hidden="true"></span><span>' +
      getLoadingLabel(button) +
      "</span>";
  }

  function handleFormSubmit(event) {
    var form = event.target;
    if (!(form instanceof HTMLFormElement)) {
      return;
    }

    var submitter = event.submitter || form.querySelector('button[type="submit"], input[type="submit"]');
    var confirmMessage = "";

    if (submitter && submitter.dataset.confirm) {
      confirmMessage = submitter.dataset.confirm;
    } else if (form.dataset.confirm) {
      confirmMessage = form.dataset.confirm;
    }

    if (confirmMessage && !window.confirm(confirmMessage)) {
      event.preventDefault();
      return;
    }

    if (submitter) {
      setButtonLoading(submitter);
    }
  }

  function dismissFlash(flash) {
    if (!flash) {
      return;
    }
    flash.classList.add("is-hiding");
    window.setTimeout(function () {
      flash.remove();
    }, 220);
  }

  function setupFlashMessages() {
    var flashes = document.querySelectorAll("[data-flash]");
    flashes.forEach(function (flash) {
      var closeButton = flash.querySelector(".flash__dismiss");
      if (closeButton) {
        closeButton.addEventListener("click", function () {
          dismissFlash(flash);
        });
      }

      window.setTimeout(function () {
        dismissFlash(flash);
      }, 5200);
    });
  }

  document.addEventListener("submit", handleFormSubmit, true);
  document.addEventListener("DOMContentLoaded", setupFlashMessages);
})();

