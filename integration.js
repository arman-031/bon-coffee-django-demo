'use strict';

(() => {
  const hasApi = Boolean(API_BASE_URL);
  let apiReady = false;
  order = null;
  try {
    localStorage.removeItem('bon-order');
  } catch {
    toast('پاک‌کردن سفارش‌های نمایشی قبلی از این مرورگر انجام نشد.');
  }
  const statusLabels = {
    pending: 'در انتظار پرداخت',
    paid: 'پرداخت شبیه‌سازی‌شده',
    preparing: 'در حال آماده‌سازی',
    shipped: 'ارسال شده',
    completed: 'تکمیل شده',
    cancelled: 'لغو شده',
  };

  const request = (url, options = {}) => {
    if (!hasApi) {
      throw new Error('نشانی API تنظیم نشده است؛ اتصال backend را پیکربندی کنید.');
    }
    return apiFetch(url, options);
  };

  const send = (url, method, body) =>
    request(url, { method, body: JSON.stringify(body) });

  function cartItemFromApi(item) {
    return {
      id: Number(item.product?.id ?? item.product_id),
      serverId: item.id,
      weight: Number(item.weight || 0),
      grind: item.grind || '',
      qty: Number(item.quantity || 1),
    };
  }

  async function loadRemoteCart() {
    const items = await request('/api/cart/');
    cart = items.map(cartItemFromApi).filter(item =>
      P.some(product => product.id === item.id),
    );
    persist();
    return cart;
  }

  async function loadRemoteFavorites() {
    const items = await request('/api/favorites/');
    wish = items
      .map(item => Number(item.product?.id ?? item.product_id))
      .filter(Number.isInteger);
    persist();
    return wish;
  }

  async function mergeGuestData() {
    let failed = false;
    const guestCart = cart.map(({ id, weight, grind, qty }) => ({
      product_id: id,
      weight,
      grind,
      quantity: qty,
    }));
    const guestFavorites = [...wish];

    for (const item of guestCart) {
      try {
        await send('/api/cart/', 'POST', item);
      } catch {
        failed = true;
      }
    }
    for (const id of guestFavorites) {
      try {
        await send('/api/favorites/', 'POST', { product_id: id });
      } catch {
        failed = true;
      }
    }

    try {
      await loadRemoteCart();
      await loadRemoteFavorites();
    } catch {
      failed = true;
    }
    return failed;
  }

  function closeModal() {
    if ($('#modal').open) $('#modal').close();
  }

  function showAuth(mode = 'login') {
    const registering = mode === 'register';
    modal(`
      <h2>${registering ? 'ساخت حساب کاربری' : 'ورود به حساب کاربری'}</h2>
      <p>ورود با حساب Django انجام می‌شود؛ هیچ کد پیامکی یا پرداخت واقعی وجود ندارد.</p>
      <form id="bonAuthForm" class="simple-form">
        ${registering ? `
          <label>نام<input name="first_name" autocomplete="given-name" required></label>
          <label>نام خانوادگی<input name="last_name" autocomplete="family-name" required></label>
          <label>ایمیل<input name="email" type="email" autocomplete="email"></label>
        ` : ''}
        <label>نام کاربری<input name="username" autocomplete="username" required></label>
        <label>رمز عبور<input name="password" type="password" autocomplete="${registering ? 'new-password' : 'current-password'}" minlength="${registering ? 8 : 1}" required></label>
        <p id="bonAuthError" class="error" role="alert"></p>
        <button class="btn">${registering ? 'ثبت‌نام' : 'ورود'}</button>
      </form>
      <button class="text-link" type="button" data-auth-mode="${registering ? 'login' : 'register'}">${registering ? 'قبلاً حساب ساخته‌اید؟ ورود' : 'حساب ندارید؟ ثبت‌نام'}</button>
    `);
  }

  function renderOrders(orders) {
    if (!orders.length) return '<p>هنوز سفارشی ثبت نشده است.</p>';
    return orders.map(item => `
      <article class="order-row">
        <b>${esc(item.order_ref)}</b>
        <span>${esc(statusLabels[item.status] || item.status)}</span>
        <b>${money(item.total)}</b>
      </article>
    `).join('');
  }

  function renderAccount(panel) {
    const user = sessionUser;
    const accountKey = user ? String(user.id) : 'guest';
    if (panel.dataset.bonAccountUser === accountKey) return;
    panel.dataset.bonAccountUser = accountKey;
    panel.innerHTML = `
      <span class="eyebrow">حساب کاربری</span>
      <h1>سلام ${esc(user ? (user.first_name || user.username) : 'به بُن خوش آمدی')}.</h1>
      ${user ? `
        <p>وضعیت ورود: ${esc(user.username)}</p>
        <div id="bonOrderList"><p>در حال دریافت سفارش‌ها…</p></div>
        <button class="btn outline" type="button" data-logout>خروج از حساب</button>
      ` : `
        <p>${hasApi ? 'برای سفارش و پیگیری، وارد حساب خود شوید.' : 'برای استفاده از حساب و ثبت سفارش، نشانی API را تنظیم کنید.'}</p>
        <button class="btn" id="bonLoginButton" type="button">ورود / ثبت‌نام</button>
        <a class="btn outline" href="#wishlist">علاقه‌مندی‌ها ♡</a>
      `}
    `;

    if (user) {
      request('/api/orders/')
        .then(orders => {
          const list = $('#bonOrderList');
          if (list) list.innerHTML = renderOrders(orders);
        })
        .catch(error => {
          const list = $('#bonOrderList');
          if (list) list.innerHTML = `<p class="error" role="alert">${esc(error.message)}</p>`;
        });
    } else {
      $('#bonLoginButton')?.addEventListener('click', () => showAuth());
    }
  }

  function enhancePage() {
    const authLink = document.querySelector('.header-actions a[href="#account"]');
    let logoutButton = $('#bonHeaderLogout');
    if (sessionUser) {
      if (authLink) authLink.textContent = sessionUser.first_name || sessionUser.username;
      if (!logoutButton) {
        logoutButton = document.createElement('button');
        logoutButton.id = 'bonHeaderLogout';
        logoutButton.className = 'text-link';
        logoutButton.type = 'button';
        logoutButton.dataset.logout = '';
        logoutButton.textContent = 'خروج';
        document.querySelector('.header-actions')?.append(logoutButton);
      }
    } else {
      if (authLink) authLink.textContent = 'ورود | ثبت‌نام';
      logoutButton?.remove();
    }

    const panel = $('#app .account-panel');
    if (location.hash === '#account' && panel) renderAccount(panel);

    if (location.hash === '#checkout') {
      const notice = $('#checkoutForm .note-box');
      if (notice) {
        notice.textContent = sessionUser
          ? 'اطلاعات این فرم برای ثبت سفارش در حساب شما به backend ارسال می‌شود.'
          : 'برای ثبت سفارش، ابتدا با حساب کاربری خود وارد شوید.';
      }
    }

    if (location.hash === '#success' && order?.order_ref) {
      const successPanel = $('#app .account-panel');
      if (successPanel) {
        successPanel.innerHTML = `
          <span class="eyebrow">✓ سفارش ثبت شد</span>
          <h1>پرداخت شبیه‌سازی‌شده انجام شد.</h1>
          <p>هیچ تراکنش بانکی یا پرداخت واقعی انجام نشده است.</p>
          <div class="order-row"><b>${esc(order.order_ref)}</b><span>${money(order.total)}</span></div>
          <a class="btn" href="#account">مشاهده سفارش‌ها</a>
          <a class="text-link" href="#tracking">پیگیری سفارش</a>
        `;
      }
    }
  }

  async function authenticate(form) {
    const values = Object.fromEntries(new FormData(form));
    const registering = form.querySelector('[name="first_name"]') !== null;
    await request('/api/auth/csrf/');
    const result = await send(
      registering ? '/api/auth/register/' : '/api/auth/login/',
      'POST',
      values,
    );
    sessionUser = result.user;

    let previousOwner = null;
    try {
      previousOwner = localStorage.getItem('bon-session-user');
    } catch {
      previousOwner = null;
    }

    let syncFailed = false;
    if (previousOwner && previousOwner !== String(sessionUser.id)) {
      cart = [];
      wish = [];
    } else if (previousOwner !== String(sessionUser.id)) {
      syncFailed = await mergeGuestData();
    } else {
      try {
        await loadRemoteCart();
        await loadRemoteFavorites();
      } catch {
        syncFailed = true;
      }
    }

    try {
      localStorage.setItem('bon-session-user', String(sessionUser.id));
      localStorage.setItem('bon-user', JSON.stringify(sessionUser));
    } catch {
      syncFailed = true;
    }
    closeModal();
    render(false);
    enhancePage();
    toast(syncFailed
      ? 'ورود انجام شد، اما همگام‌سازی بخشی از اطلاعات کامل نشد.'
      : registering ? 'ثبت‌نام و ورود انجام شد.' : 'ورود موفق بود.');
  }

  async function logout() {
    await send('/api/auth/logout/', 'POST', {});
    sessionUser = null;
    cart = [];
    wish = [];
    persist();
    try {
      localStorage.removeItem('bon-session-user');
      localStorage.removeItem('bon-user');
    } catch {
      toast('از حساب خارج شدید، اما پاک‌کردن وضعیت محلی مرورگر ممکن نشد.');
    }
    render(false);
    enhancePage();
    toast('از حساب خارج شدید.');
  }

  async function toggleFavorite(button) {
    const id = Number(button.dataset.wish);
    if (wish.includes(id)) {
      await request(`/api/favorites/${id}/`, { method: 'DELETE' });
    } else {
      await send('/api/favorites/', 'POST', { product_id: id });
    }
    await loadRemoteFavorites();
    document.querySelectorAll(`[data-wish="${id}"]`).forEach(item => {
      item.classList.toggle('active', wish.includes(id));
      item.setAttribute('aria-pressed', String(wish.includes(id)));
    });
    if (location.hash.startsWith('#wishlist')) render(false);
    toast(wish.includes(id) ? 'به علاقه‌مندی‌ها اضافه شد.' : 'از علاقه‌مندی‌ها حذف شد.');
  }

  async function addRemoteCart(button) {
    const productId = Number(button.dataset.add);
    const product = P.find(item => item.id === productId);
    const weight = product?.isCoffee ? currentWeight : 0;
    const grind = product?.isCoffee ? $('#grindSelect')?.value : 'بسته اصلی';
    if (!product || !product.stock) throw new Error('این محصول موجود نیست.');
    if (product.isCoffee && !grind) throw new Error('ابتدا نوع قهوه یا آسیاب را انتخاب کنید.');
    await send('/api/cart/', 'POST', {
      product_id: productId,
      quantity: 1,
      weight,
      grind,
    });
    await loadRemoteCart();
    toast('محصول در سبد خرید حساب شما ذخیره شد.');
  }

  async function updateRemoteCart(button) {
    const lineKey = button.dataset.line || button.dataset.remove;
    const item = cart.find(entry => key(entry) === lineKey);
    if (!item?.serverId) throw new Error('آیتم سبد خرید همگام نیست؛ صفحه را تازه‌سازی کنید.');

    if (button.dataset.remove !== undefined) {
      await request('/api/cart/', {
        method: 'DELETE',
        body: JSON.stringify({ id: item.serverId }),
      });
    } else {
      const quantity = item.qty + Number(button.dataset.delta);
      if (quantity < 1) {
        await request('/api/cart/', {
          method: 'DELETE',
          body: JSON.stringify({ id: item.serverId }),
        });
      } else {
        await send('/api/cart/', 'PATCH', { id: item.serverId, quantity });
      }
    }

    await loadRemoteCart();
    render(false);
  }

  function toAsciiDigits(value) {
    return String(value)
      .replace(/[۰-۹]/g, digit => '۰۱۲۳۴۵۶۷۸۹'.indexOf(digit))
      .replace(/[٠-٩]/g, digit => '٠١٢٣٤٥٦٧٨٩'.indexOf(digit));
  }

  async function submitCheckout(form) {
    const errorBox = $('#checkoutError');
    if (!sessionUser) {
      if (errorBox) errorBox.textContent = 'برای ثبت سفارش، ابتدا وارد حساب شوید.';
      showAuth();
      return;
    }

    const values = Object.fromEntries(new FormData(form));
    const phone = toAsciiDigits(values.phone).trim();
    const postalCode = toAsciiDigits(values.postal).trim();
    if (!/^09\d{9}$/.test(phone)) {
      if (errorBox) errorBox.textContent = 'شماره همراه باید ۱۱ رقم باشد و با ۰۹ شروع شود.';
      return;
    }
    if (!/^\d{10}$/.test(postalCode)) {
      if (errorBox) errorBox.textContent = 'کد پستی باید ۱۰ رقم باشد.';
      return;
    }

    let createdOrder = null;
    try {
      createdOrder = await send('/api/orders/create/', 'POST', {
        customer_name: values.name,
        phone,
        city: [values.province, values.city].filter(Boolean).join('، '),
        address: values.address,
        postal_code: postalCode,
        coupon_code: coupon ? C.coupon : '',
        items: cart.map(item => ({
          product_id: item.id,
          quantity: item.qty,
          weight: item.weight,
          grind: item.grind,
        })),
      });
      const payment = await send('/api/payments/simulated/', 'POST', {
        order_id: createdOrder.id,
      });
      if (!payment?.is_simulated) {
        throw new Error('پاسخ پرداخت شبیه‌سازی‌شده تأیید نشد.');
      }
      order = {
        ...createdOrder,
        status: 'paid',
        paid_at: new Date().toISOString(),
        id: createdOrder.order_ref,
        date: new Date(createdOrder.created_at).toLocaleDateString('fa-IR'),
      };
      cart = [];
      coupon = false;
      persist();
      location.hash = 'success';
    } catch (error) {
      if (errorBox) {
        errorBox.textContent = createdOrder
          ? `سفارش ${createdOrder.order_ref} ایجاد شد، اما پرداخت نمایشی تأیید نشد. سبد خرید حفظ شد. ${error.message}`
          : error.message;
      }
    }
  }

  async function trackOrder(form) {
    const result = $('#trackResult');
    if (!sessionUser) {
      if (result) result.innerHTML = '<p class="error">برای پیگیری، ابتدا وارد حساب خود شوید.</p>';
      showAuth();
      return;
    }
    const reference = $('#orderId').value.trim().toUpperCase();
    try {
      const orders = await request('/api/orders/');
      const found = orders.find(item => item.order_ref.toUpperCase() === reference);
      if (!result) return;
      result.innerHTML = found
        ? `<div class="order-row"><b>${esc(found.order_ref)}</b><span>${esc(statusLabels[found.status] || found.status)}</span><b>${money(found.total)}</b></div>`
        : '<p class="error">این سفارش در حساب شما پیدا نشد.</p>';
    } catch (error) {
      if (result) result.innerHTML = `<p class="error" role="alert">${esc(error.message)}</p>`;
    }
  }

  document.addEventListener('click', event => {
    const target = event.target.closest('#demoLogin,#bonLoginButton,[data-auth-mode],[data-logout],[data-wish],[data-add],[data-line],[data-remove]');
    if (!target) return;

    if (target.id === 'demoLogin' || target.id === 'bonLoginButton') {
      event.preventDefault();
      event.stopImmediatePropagation();
      showAuth();
      return;
    }
    if (target.dataset.authMode) {
      event.preventDefault();
      event.stopImmediatePropagation();
      showAuth(target.dataset.authMode);
      return;
    }

    if (hasApi && !apiReady && (
      target.hasAttribute('data-wish')
      || target.hasAttribute('data-add')
      || target.hasAttribute('data-line')
      || target.hasAttribute('data-remove')
    )) {
      event.preventDefault();
      event.stopImmediatePropagation();
      toast('اتصال API آماده نیست؛ این عملیات انجام نشد.');
      return;
    }

    const operation = target.hasAttribute('data-logout')
      ? logout
      : target.hasAttribute('data-wish') && sessionUser
        ? () => toggleFavorite(target)
        : target.hasAttribute('data-add') && sessionUser
          ? () => addRemoteCart(target)
          : (target.hasAttribute('data-line') || target.hasAttribute('data-remove')) && sessionUser
            ? () => updateRemoteCart(target)
            : null;
    if (!operation) return;

    event.preventDefault();
    event.stopImmediatePropagation();
    operation().catch(error => toast(error.message));
  }, true);

  document.addEventListener('submit', event => {
    const form = event.target;
    if (form.id === 'bonAuthForm') {
      event.preventDefault();
      event.stopImmediatePropagation();
      const errorBox = $('#bonAuthError');
      authenticate(form).catch(error => {
        if (errorBox) errorBox.textContent = error.message;
      });
    } else if (form.id === 'checkoutForm') {
      event.preventDefault();
      event.stopImmediatePropagation();
      submitCheckout(form).catch(error => {
        const errorBox = $('#checkoutError');
        if (errorBox) errorBox.textContent = error.message;
      });
    } else if (form.id === 'trackForm') {
      event.preventDefault();
      event.stopImmediatePropagation();
      trackOrder(form);
    }
  }, true);

  window.addEventListener('hashchange', enhancePage);
  new MutationObserver(enhancePage).observe(app, { childList: true });

  async function initialize() {
    if (!hasApi) {
      if (location.hash === '#success') location.hash = 'account';
      enhancePage();
      return;
    }
    try {
      await request('/api/auth/csrf/');
      apiReady = true;
      sessionUser = await request('/api/auth/profile/');
    } catch {
      sessionUser = null;
    }

    let storedOwner = null;
    try {
      storedOwner = localStorage.getItem('bon-session-user');
    } catch {
      storedOwner = null;
    }
    if (sessionUser) {
      let syncFailed = false;
      if (storedOwner && storedOwner !== String(sessionUser.id)) {
        cart = [];
        wish = [];
      }
      if (storedOwner !== String(sessionUser.id)) {
        syncFailed = await mergeGuestData();
      } else {
        try {
          await loadRemoteCart();
          await loadRemoteFavorites();
        } catch {
          syncFailed = true;
        }
      }
      try {
        localStorage.setItem('bon-session-user', String(sessionUser.id));
        localStorage.setItem('bon-user', JSON.stringify(sessionUser));
      } catch {
        syncFailed = true;
      }
      if (syncFailed) toast('حساب وارد شد، اما همگام‌سازی بخشی از اطلاعات انجام نشد.');
    } else if (location.hash === '#success') {
      location.hash = 'account';
    }
    enhancePage();
  }

  initialize();
})();
