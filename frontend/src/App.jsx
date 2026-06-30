import { useEffect, useState } from "react";
import "./App.css";

const API_URL =
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8000"
    : window.location.origin;

const initialOrderForm = {
  customer_name: "",
  last_name: "",
  middle_name: "",
  phone: "",
  email: "",
  telegram_id: "",
  telegram_username: "",
  quantity: 1,
  shipping_method: "novaposhta",
  payment_method: "Накладений платіж",
  city: "",
  warehouse: "",
  city_ref: "",
  warehouse_ref: "",
  comment: "",
};

function App() {
  const [products, setProducts] = useState([]);
  const [productsLoading, setProductsLoading] = useState(false);
  const [error, setError] = useState("");

  const [selectedProduct, setSelectedProduct] = useState(null);
  const [orderForm, setOrderForm] = useState(initialOrderForm);

  const [cartItems, setCartItems] = useState([]);
  const [checkoutItems, setCheckoutItems] = useState([]);
  const [cartOpen, setCartOpen] = useState(false);

  const [submitting, setSubmitting] = useState(false);
  const [orderResult, setOrderResult] = useState(null);
  const [paymentUrl, setPaymentUrl] = useState("");

  const [npCities, setNpCities] = useState([]);
  const [npWarehouses, setNpWarehouses] = useState([]);

  const [rozetkaCities, setRozetkaCities] = useState([]);
  const [rozetkaDepartments, setRozetkaDepartments] = useState([]);

  const [ukrposhtaCities, setUkrposhtaCities] = useState([]);
  const [ukrposhtaOffices, setUkrposhtaOffices] = useState([]);

  const [deliveryLoading, setDeliveryLoading] = useState(false);

  useEffect(() => {
    loadProducts();
  }, []);

  useEffect(() => {
    const savedCart = localStorage.getItem("telegram_shop_cart");

    if (savedCart) {
      try {
        const parsedCart = JSON.parse(savedCart);
        setCartItems(Array.isArray(parsedCart) ? parsedCart : []);
      } catch (error) {
        console.error("Cart parse error:", error);
        setCartItems([]);
      }
    }
  }, []);

  useEffect(() => {
    localStorage.setItem("telegram_shop_cart", JSON.stringify(cartItems));
  }, [cartItems]);

  function isNovaPoshtaDelivery(method) {
    return method === "novaposhta";
  }

  function isRozetkaDelivery(method) {
    return method === "rozetka";
  }

  function isUkrposhtaDelivery(method) {
    return method === "ukrposhta";
  }

  function getTelegramUser() {
    const telegram = window.Telegram?.WebApp;

    if (!telegram) {
      return null;
    }

    try {
      telegram.ready?.();
      telegram.expand?.();
    } catch (error) {
      console.warn("Telegram WebApp init warning:", error);
    }

    return telegram.initDataUnsafe?.user || null;
  }

  async function loadProducts() {
    try {
      setProductsLoading(true);
      setError("");

      const response = await fetch(`${API_URL}/products`);

      if (!response.ok) {
        throw new Error("Не вдалося завантажити товари");
      }

      const data = await response.json();
      setProducts(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Products loading error:", error);
      setError(error.message || "Failed to fetch");
    } finally {
      setProductsLoading(false);
    }
  }

  function resetDeliveryLists() {
    setNpCities([]);
    setNpWarehouses([]);
    setRozetkaCities([]);
    setRozetkaDepartments([]);
    setUkrposhtaCities([]);
    setUkrposhtaOffices([]);
  }

  function openOrderModal(product) {
    const telegramUser = getTelegramUser();

    setSelectedProduct(product);

    setOrderForm({
      ...initialOrderForm,
      customer_name: telegramUser?.first_name || "",
      last_name: telegramUser?.last_name || "",
      telegram_id: telegramUser?.id ? String(telegramUser.id) : "",
      telegram_username: telegramUser?.username || "",
    });

    setOrderResult(null);
    setPaymentUrl("");
    setCheckoutItems([]);
    setError("");
    resetDeliveryLists();
  }

  function closeOrderModal() {
    setSelectedProduct(null);
    setOrderResult(null);
    setPaymentUrl("");
    setCheckoutItems([]);
    setError("");
    resetDeliveryLists();
  }

  function openCheckoutFromCart() {
    if (cartItems.length === 0) {
      setError("Кошик порожній");
      return;
    }

    const telegramUser = getTelegramUser();

    const itemsSnapshot = cartItems.map((item) => ({
      ...item,
      id: Number(item.id),
      price: Number(item.price || 0),
      quantity: Number(item.quantity || 1),
    }));

    const itemsCount = itemsSnapshot.reduce(
      (total, item) => total + Number(item.quantity || 1),
      0
    );

    const itemsTotal = itemsSnapshot.reduce(
      (total, item) =>
        total + Number(item.price || 0) * Number(item.quantity || 1),
      0
    );

    setCheckoutItems(itemsSnapshot);

    setSelectedProduct({
      id: "cart",
      name: `Замовлення з кошика (${itemsCount} шт.)`,
      price: itemsTotal,
    });

    setOrderForm({
      ...initialOrderForm,
      customer_name: telegramUser?.first_name || "",
      last_name: telegramUser?.last_name || "",
      telegram_id: telegramUser?.id ? String(telegramUser.id) : "",
      telegram_username: telegramUser?.username || "",
    });

    setOrderResult(null);
    setPaymentUrl("");
    setError("");
    resetDeliveryLists();
    setCartOpen(false);
  }

  function handleChange(event) {
    const { name, value } = event.target;

    if (name === "shipping_method") {
      resetDeliveryLists();

      setOrderForm((prev) => ({
        ...prev,
        shipping_method: value,
        payment_method:
          value === "ukrposhta" && prev.payment_method === "Накладений платіж"
            ? "WayForPay"
            : prev.payment_method,
        city: "",
        warehouse: "",
        city_ref: "",
        warehouse_ref: "",
      }));

      return;
    }

    if (name === "payment_method") {
      setOrderForm((prev) => ({
        ...prev,
        payment_method: value,
      }));

      return;
    }

    setOrderForm((prev) => ({
      ...prev,
      [name]: value,
    }));

    if (name === "city") {
      resetDeliveryLists();

      if (isNovaPoshtaDelivery(orderForm.shipping_method)) {
        searchNovaPoshtaCities(value);
      }

      if (isRozetkaDelivery(orderForm.shipping_method)) {
        searchRozetkaCities(value);
      }

      if (isUkrposhtaDelivery(orderForm.shipping_method)) {
        searchUkrposhtaCities(value);
      }
    }
  }

  async function searchNovaPoshtaCities(cityName) {
    if (!cityName || cityName.trim().length < 2) {
      setNpCities([]);
      return;
    }

    try {
      setDeliveryLoading(true);

      const response = await fetch(
        `${API_URL}/novaposhta/cities?city=${encodeURIComponent(cityName)}`
      );

      const data = await response.json();
      const addresses = data?.data?.[0]?.Addresses || [];

      setNpCities(addresses);
    } catch (error) {
      console.error("Nova Poshta city search error:", error);
      setNpCities([]);
    } finally {
      setDeliveryLoading(false);
    }
  }

  async function selectNovaPoshtaCity(city) {
    const cityName = city.Present || city.MainDescription || "";
    const cityRef = city.DeliveryCity || city.Ref || "";

    setOrderForm((prev) => ({
      ...prev,
      city: cityName,
      city_ref: cityRef,
      warehouse: "",
      warehouse_ref: "",
    }));

    setNpCities([]);
    setNpWarehouses([]);

    if (!cityRef) {
      return;
    }

    try {
      setDeliveryLoading(true);

      const response = await fetch(
        `${API_URL}/novaposhta/warehouses?city_ref=${encodeURIComponent(
          cityRef
        )}&limit=500`
      );

      const data = await response.json();
      setNpWarehouses(data?.warehouses || []);
    } catch (error) {
      console.error("Nova Poshta warehouses error:", error);
      setNpWarehouses([]);
    } finally {
      setDeliveryLoading(false);
    }
  }

  function getNovaPoshtaWarehouseDescription(warehouse) {
    return (
      warehouse.description ||
      warehouse.Description ||
      warehouse.short_address ||
      warehouse.ShortAddress ||
      warehouse.address ||
      warehouse.Address ||
      "Відділення Нової пошти"
    );
  }

  function getNovaPoshtaWarehouseValue(warehouse) {
    const explicitValue =
      warehouse.number ||
      warehouse.Number ||
      warehouse.warehouse_number ||
      warehouse.WarehouseNumber ||
      warehouse.site_key ||
      warehouse.SiteKey;

    if (explicitValue) {
      return String(explicitValue);
    }

    const description = getNovaPoshtaWarehouseDescription(warehouse);
    const numberMatch = description.match(/№\s*([0-9]+)/);

    if (numberMatch) {
      return numberMatch[1];
    }

    return String(warehouse.ref || warehouse.Ref || "");
  }

  function selectNovaPoshtaWarehouse(warehouse) {
    const warehouseDescription = getNovaPoshtaWarehouseDescription(warehouse);
    const warehouseValue = getNovaPoshtaWarehouseValue(warehouse);

    setOrderForm((prev) => ({
      ...prev,
      warehouse: warehouseDescription,
      warehouse_ref: warehouseValue,
    }));
  }

  async function searchUkrposhtaCities(cityName) {
    if (!cityName || cityName.trim().length < 2) {
      setUkrposhtaCities([]);
      return;
    }

    try {
      setDeliveryLoading(true);

      const response = await fetch(
        `${API_URL}/ukrposhta/cities?city=${encodeURIComponent(cityName)}`
      );

      const data = await response.json();
      setUkrposhtaCities(data?.cities || []);
    } catch (error) {
      console.error("Ukrposhta city search error:", error);
      setUkrposhtaCities([]);
    } finally {
      setDeliveryLoading(false);
    }
  }

  async function selectUkrposhtaCity(city) {
    const cityName = city.label || city.name || "";
    const cityId = city.id || "";
    const cityKoatuu = city.koatuu || "";
    const cityKatottg = city.katottg || "";

    setOrderForm((prev) => ({
      ...prev,
      city: cityName,
      city_ref: cityId,
      warehouse: "",
      warehouse_ref: "",
    }));

    setUkrposhtaCities([]);
    setUkrposhtaOffices([]);

    try {
      setDeliveryLoading(true);

      const params = new URLSearchParams();

      if (cityId) params.append("city_id", cityId);
      if (cityKoatuu) params.append("city_koatuu", cityKoatuu);
      if (cityKatottg) params.append("city_katottg", cityKatottg);

      const response = await fetch(
        `${API_URL}/ukrposhta/offices?${params.toString()}`
      );

      const data = await response.json();
      setUkrposhtaOffices(data?.offices || []);
    } catch (error) {
      console.error("Ukrposhta offices error:", error);
      setUkrposhtaOffices([]);
    } finally {
      setDeliveryLoading(false);
    }
  }

  function selectUkrposhtaOffice(office) {
    const postcode = office.postcode || "";
    const description = office.description || postcode || "Відділення Укрпошти";

    setOrderForm((prev) => ({
      ...prev,
      warehouse: description,
      warehouse_ref: postcode,
    }));
  }

  async function searchRozetkaCities(cityName) {
    if (!cityName || cityName.trim().length < 2) {
      setRozetkaCities([]);
      return;
    }

    try {
      setDeliveryLoading(true);

      const response = await fetch(
        `${API_URL}/rozetka/cities?city=${encodeURIComponent(cityName)}`
      );

      const data = await response.json();

      const cities = Array.isArray(data?.data)
        ? data.data
        : Array.isArray(data?.cities)
        ? data.cities
        : [];

      const normalizedSearch = normalizeCityName(cityName);

      const filteredCities = cities
        .filter((city) => {
          const name = normalizeCityName(city.name || city.title || "");
          return name.includes(normalizedSearch);
        })
        .sort((a, b) => {
          const nameA = normalizeCityName(a.name || a.title || "");
          const nameB = normalizeCityName(b.name || b.title || "");

          const aExact = nameA === normalizedSearch ? 0 : 1;
          const bExact = nameB === normalizedSearch ? 0 : 1;

          if (aExact !== bExact) {
            return aExact - bExact;
          }

          const aStarts = nameA.startsWith(normalizedSearch) ? 0 : 1;
          const bStarts = nameB.startsWith(normalizedSearch) ? 0 : 1;

          if (aStarts !== bStarts) {
            return aStarts - bStarts;
          }

          return nameA.localeCompare(nameB, "uk");
        });

      setRozetkaCities(filteredCities.slice(0, 30));
    } catch (error) {
      console.error("Rozetka city search error:", error);
      setRozetkaCities([]);
    } finally {
      setDeliveryLoading(false);
    }
  }

  function normalizeCityName(value) {
    return String(value || "")
      .toLowerCase()
      .replace(/^м\.\s*/i, "")
      .replace(/^с\.\s*/i, "")
      .replace(/^смт\.\s*/i, "")
      .trim();
  }

  async function selectRozetkaCity(city) {
    const cityName = city.name || city.title || "";
    const cityRef = city.id || city.uuid || city.ref || "";

    setOrderForm((prev) => ({
      ...prev,
      city: cityName,
      city_ref: cityRef,
      warehouse: "",
      warehouse_ref: "",
    }));

    setRozetkaCities([]);
    setRozetkaDepartments([]);

    if (!cityRef) {
      return;
    }

    try {
      setDeliveryLoading(true);

      const response = await fetch(
        `${API_URL}/rozetka/departments?city_id=${encodeURIComponent(cityRef)}`
      );

      const data = await response.json();

      const departments = Array.isArray(data?.data)
        ? data.data
        : Array.isArray(data?.departments)
        ? data.departments
        : [];

      setRozetkaDepartments(departments);
    } catch (error) {
      console.error("Rozetka departments error:", error);
      setRozetkaDepartments([]);
    } finally {
      setDeliveryLoading(false);
    }
  }

  function selectRozetkaDepartment(department) {
    const departmentId = String(
      department.id || department.uuid || department.ref || ""
    );

    const departmentName =
      department.name ||
      department.title ||
      department.public_name ||
      department.address ||
      "Точка видачі Rozetka";

    setOrderForm((prev) => ({
      ...prev,
      warehouse: departmentName,
      warehouse_ref: departmentId,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (checkoutItems.length === 0) {
      setError("Кошик порожній");
      return;
    }

    if (!orderForm.customer_name.trim()) {
      setError("Вкажіть ім’я");
      return;
    }

    if (!orderForm.phone.trim()) {
      setError("Вкажіть телефон");
      return;
    }

    if (!orderForm.city.trim()) {
      setError("Оберіть або введіть місто");
      return;
    }

    if (!orderForm.warehouse.trim()) {
      setError("Оберіть або введіть відділення / точку видачі / індекс");
      return;
    }

    if (
      isUkrposhtaDelivery(orderForm.shipping_method) &&
      orderForm.payment_method === "Накладений платіж"
    ) {
      setError("Для Укрпошти накладений платіж поки недоступний");
      return;
    }

    try {
      setSubmitting(true);
      setError("");
      setOrderResult(null);
      setPaymentUrl("");

      const payload = {
        customer_name: orderForm.customer_name,
        last_name: orderForm.last_name,
        middle_name: orderForm.middle_name,
        phone: orderForm.phone,
        email: orderForm.email,
        telegram_id: orderForm.telegram_id || null,
        telegram_username: orderForm.telegram_username || "",

        items: checkoutItems.map((item) => ({
          product_id: Number(item.id),
          quantity: Number(item.quantity) || 1,
        })),

        city: orderForm.city,
        warehouse: orderForm.warehouse,

        city_ref: isUkrposhtaDelivery(orderForm.shipping_method)
          ? null
          : orderForm.city_ref || null,

        warehouse_ref: isUkrposhtaDelivery(orderForm.shipping_method)
          ? orderForm.warehouse_ref || orderForm.warehouse.trim()
          : orderForm.warehouse_ref || null,

        payment_method: orderForm.payment_method,
        shipping_method: orderForm.shipping_method,
        comment: orderForm.comment,
      };

      console.log("Order payload:", payload);

      const response = await fetch(`${API_URL}/orders`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.detail || "Не вдалося створити замовлення");
      }

      setOrderResult(data);
      clearCart();

      if (orderForm.payment_method === "WayForPay" && data?.order_id) {
        const paymentResponse = await fetch(
          `${API_URL}/orders/${data.order_id}/payment-url`
        );

        const paymentData = await paymentResponse.json();

        if (paymentData?.payment_url) {
          setPaymentUrl(paymentData.payment_url);
        }
      }
    } catch (error) {
      console.error("Order submit error:", error);
      setError(error.message || "Помилка створення замовлення");
    } finally {
      setSubmitting(false);
    }
  }

  function addToCart(product) {
    setCartItems((prev) => {
      const existingItem = prev.find((item) => item.id === product.id);

      if (existingItem) {
        return prev.map((item) =>
          item.id === product.id
            ? {
                ...item,
                quantity: Number(item.quantity || 1) + 1,
              }
            : item
        );
      }

      return [
        ...prev,
        {
          id: product.id,
          name: getProductName(product),
          price: getProductPrice(product),
          quantity: 1,
        },
      ];
    });

    setCartOpen(true);
  }

  function increaseCartItem(productId) {
    setCartItems((prev) =>
      prev.map((item) =>
        item.id === productId
          ? {
              ...item,
              quantity: Number(item.quantity || 1) + 1,
            }
          : item
      )
    );
  }

  function decreaseCartItem(productId) {
    setCartItems((prev) =>
      prev
        .map((item) =>
          item.id === productId
            ? {
                ...item,
                quantity: Number(item.quantity || 1) - 1,
              }
            : item
        )
        .filter((item) => item.quantity > 0)
    );
  }

  function removeCartItem(productId) {
    setCartItems((prev) => prev.filter((item) => item.id !== productId));
  }

  function clearCart() {
    setCartItems([]);
  }

  function getCartTotal() {
    return cartItems.reduce(
      (total, item) =>
        total + Number(item.price || 0) * Number(item.quantity || 1),
      0
    );
  }

  function getCartItemsCount() {
    return cartItems.reduce(
      (total, item) => total + Number(item.quantity || 1),
      0
    );
  }

  function getProductPrice(product) {
    return product.price || product.cost || 0;
  }

  function getProductName(product) {
    return product.name || product.title || "Товар";
  }

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>Telegram-магазин MyCar</h1>
          <p>Каталог товарів</p>
        </div>

        <button
          type="button"
          className="cart-button"
          onClick={() => setCartOpen(true)}
        >
          🛒 Кошик
          {getCartItemsCount() > 0 && (
            <span className="cart-count">{getCartItemsCount()}</span>
          )}
        </button>
      </header>

      <main className="main">
        {error && <div className="error-message">{error}</div>}

        {productsLoading ? (
          <p className="loading-text">Завантаження товарів...</p>
        ) : (
          <div className="products-grid">
            {products.map((product) => (
              <div className="product-card" key={product.id}>
                <div className="product-image">Фото товару</div>

                <h2>{getProductName(product)}</h2>

                <div className="product-price">
                  {getProductPrice(product)} грн
                </div>

                <div className="product-status">В наявності</div>

                <button
                  type="button"
                  className="order-button"
                  onClick={() => addToCart(product)}
                >
                  Додати в кошик
                </button>
              </div>
            ))}
          </div>
        )}
      </main>

      {cartOpen && (
        <div className="modal-backdrop">
          <div className="order-modal">
            <button
              type="button"
              className="modal-close"
              onClick={() => setCartOpen(false)}
            >
              ×
            </button>

            <h2 className="modal-title">Кошик</h2>

            {cartItems.length === 0 ? (
              <div className="empty-cart">
                <p>Кошик порожній.</p>
              </div>
            ) : (
              <>
                <div className="cart-list">
                  {cartItems.map((item) => (
                    <div className="cart-item" key={item.id}>
                      <div className="cart-item-info">
                        <strong>{item.name}</strong>
                        <span>{item.price} грн</span>
                      </div>

                      <div className="cart-item-controls">
                        <button
                          type="button"
                          onClick={() => decreaseCartItem(item.id)}
                        >
                          −
                        </button>

                        <span>{item.quantity}</span>

                        <button
                          type="button"
                          onClick={() => increaseCartItem(item.id)}
                        >
                          +
                        </button>
                      </div>

                      <div className="cart-item-total">
                        {Number(item.price || 0) * Number(item.quantity || 1)} грн
                      </div>

                      <button
                        type="button"
                        className="cart-remove"
                        onClick={() => removeCartItem(item.id)}
                      >
                        Видалити
                      </button>
                    </div>
                  ))}
                </div>

                <div className="cart-summary">
                  <strong>Разом: {getCartTotal()} грн</strong>
                </div>

                <div className="cart-actions">
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={clearCart}
                  >
                    Очистити кошик
                  </button>

                  <button
                    type="button"
                    className="submit-button"
                    onClick={openCheckoutFromCart}
                  >
                    Оформити замовлення
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {selectedProduct && (
        <div className="modal-backdrop">
          <div className="order-modal">
            <button
              type="button"
              className="modal-close"
              onClick={closeOrderModal}
            >
              ×
            </button>

            <h2 className="modal-title">Оформлення замовлення</h2>

            <div className="selected-product">
              <strong>{getProductName(selectedProduct)}</strong>
              <span>{getProductPrice(selectedProduct)} грн</span>
            </div>

            {orderResult ? (
              <div className="success-message">
                <strong>✅ Дякуємо! Ваше замовлення прийнято.</strong>
                <p>Відправка відбудеться вже сьогодні.</p>
                <p>Наш менеджер зв’яжеться з вами за потреби.</p>

                {orderResult.order_id && (
                  <p>Номер замовлення: {orderResult.order_id}</p>
                )}
              </div>
            ) : (
              <form className="order-form" onSubmit={handleSubmit}>
                <div className="form-row">
                  <label>
                    Ім’я *
                    <input
                      name="customer_name"
                      value={orderForm.customer_name}
                      onChange={handleChange}
                      autoComplete="given-name"
                    />
                  </label>

                  <label>
                    Прізвище
                    <input
                      name="last_name"
                      value={orderForm.last_name}
                      onChange={handleChange}
                      autoComplete="family-name"
                    />
                  </label>
                </div>

                <div className="form-row">
                  <label>
                    По-батькові
                    <input
                      name="middle_name"
                      value={orderForm.middle_name}
                      onChange={handleChange}
                    />
                  </label>

                  <label>
                    Телефон *
                    <input
                      name="phone"
                      value={orderForm.phone}
                      onChange={handleChange}
                      placeholder="+380..."
                      autoComplete="tel"
                    />
                  </label>
                </div>

                <label>
                  Email
                  <input
                    name="email"
                    value={orderForm.email}
                    onChange={handleChange}
                    autoComplete="email"
                  />
                </label>

                <div className="form-row">
                  <label>
                    Спосіб доставки *
                    <select
                      name="shipping_method"
                      value={orderForm.shipping_method}
                      onChange={handleChange}
                    >
                      <option value="novaposhta">Нова пошта</option>
                      <option value="rozetka">Rozetka Delivery</option>
                      <option value="ukrposhta">Укрпошта</option>
                    </select>
                  </label>

                  <label>
                    Спосіб оплати *
                    <select
                      name="payment_method"
                      value={orderForm.payment_method}
                      onChange={handleChange}
                    >
                      <option
                        value="Накладений платіж"
                        disabled={isUkrposhtaDelivery(orderForm.shipping_method)}
                      >
                        Накладений платіж
                      </option>

                      <option value="WayForPay">WayForPay</option>

                      <option value="Оплата на рахунок">
                        Оплата на рахунок
                      </option>
                    </select>
                  </label>
                </div>

                <div className="form-row">
                  <label>
                    Місто / населений пункт
                    <input
                      name="city"
                      value={orderForm.city}
                      onChange={handleChange}
                      placeholder={
                        isNovaPoshtaDelivery(orderForm.shipping_method)
                          ? "Почніть вводити місто Нової пошти"
                          : isRozetkaDelivery(orderForm.shipping_method)
                          ? "Почніть вводити місто Rozetka"
                          : "Почніть вводити місто або село"
                      }
                    />
                  </label>

                  <label>
                    {isUkrposhtaDelivery(orderForm.shipping_method)
                      ? "Індекс відділення Укрпошти"
                      : "Відділення / точка видачі"}

                    {isNovaPoshtaDelivery(orderForm.shipping_method) ? (
                      <select
                        value={String(orderForm.warehouse_ref || "")}
                        onChange={(event) => {
                          const selectedWarehouse = npWarehouses.find(
                            (warehouse) =>
                              getNovaPoshtaWarehouseValue(warehouse) ===
                              event.target.value
                          );

                          if (selectedWarehouse) {
                            selectNovaPoshtaWarehouse(selectedWarehouse);
                          }
                        }}
                      >
                        <option value="">
                          Оберіть відділення або поштомат
                        </option>

                        {npWarehouses.map((warehouse, index) => {
                          const warehouseValue =
                            getNovaPoshtaWarehouseValue(warehouse);
                          const warehouseDescription =
                            getNovaPoshtaWarehouseDescription(warehouse);

                          return (
                            <option
                              key={warehouse.ref || warehouse.Ref || `${warehouseValue}-${index}`}
                              value={warehouseValue}
                            >
                              {warehouseDescription}
                            </option>
                          );
                        })}
                      </select>
                    ) : isRozetkaDelivery(orderForm.shipping_method) ? (
                      <select
                        value={orderForm.warehouse_ref}
                        onChange={(event) => {
                          const selectedDepartment = rozetkaDepartments.find(
                            (department) => {
                              const departmentId = String(
                                department.id ||
                                  department.uuid ||
                                  department.ref ||
                                  ""
                              );

                              return departmentId === event.target.value;
                            }
                          );

                          if (selectedDepartment) {
                            selectRozetkaDepartment(selectedDepartment);
                          }
                        }}
                      >
                        <option value="">Оберіть точку видачі Rozetka</option>

                        {rozetkaDepartments.map((department) => {
                          const departmentId = String(
                            department.id ||
                              department.uuid ||
                              department.ref ||
                              ""
                          );

                          const departmentName =
                            department.name ||
                            department.title ||
                            department.public_name ||
                            department.address ||
                            "Точка видачі Rozetka";

                          return (
                            <option key={departmentId} value={departmentId}>
                              {departmentName}
                            </option>
                          );
                        })}
                      </select>
                    ) : (
                      <select
                        value={orderForm.warehouse_ref}
                        onChange={(event) => {
                          const selectedOffice = ukrposhtaOffices.find(
                            (office) =>
                              String(office.postcode) === event.target.value
                          );

                          if (selectedOffice) {
                            selectUkrposhtaOffice(selectedOffice);
                          }
                        }}
                      >
                        <option value="">Оберіть відділення Укрпошти</option>

                        {ukrposhtaOffices.map((office) => (
                          <option key={office.postcode} value={office.postcode}>
                            {office.description}
                          </option>
                        ))}
                      </select>
                    )}
                  </label>
                </div>

                {isNovaPoshtaDelivery(orderForm.shipping_method) &&
                  npCities.length > 0 && (
                    <div className="suggestions">
                      {npCities.map((city) => (
                        <button
                          type="button"
                          key={city.DeliveryCity || city.Ref}
                          onClick={() => selectNovaPoshtaCity(city)}
                        >
                          {city.Present || city.MainDescription}
                        </button>
                      ))}
                    </div>
                  )}

                {isUkrposhtaDelivery(orderForm.shipping_method) &&
                  ukrposhtaCities.length > 0 && (
                    <div className="suggestions">
                      {ukrposhtaCities.map((city) => (
                        <button
                          type="button"
                          key={city.id || city.koatuu || city.katottg}
                          onClick={() => selectUkrposhtaCity(city)}
                        >
                          {city.label || city.name}
                        </button>
                      ))}
                    </div>
                  )}

                {isRozetkaDelivery(orderForm.shipping_method) &&
                  rozetkaCities.length > 0 && (
                    <div className="suggestions">
                      {rozetkaCities.map((city) => {
                        const cityId = String(
                          city.id || city.uuid || city.ref || ""
                        );

                        const cityName =
                          city.name ||
                          city.title ||
                          city.public_name ||
                          "Місто Rozetka";

                        const regionName = city.region_name
                          ? `, ${city.region_name} обл.`
                          : "";

                        return (
                          <button
                            type="button"
                            key={cityId}
                            onClick={() => selectRozetkaCity(city)}
                          >
                            {cityName}
                            {regionName}
                          </button>
                        );
                      })}
                    </div>
                  )}

                {deliveryLoading && (
                  <p className="delivery-loading">Завантаження доставки...</p>
                )}

                <label>
                  Коментар
                  <textarea
                    name="comment"
                    value={orderForm.comment}
                    onChange={handleChange}
                    rows="4"
                  />
                </label>

                <button
                  type="submit"
                  className="submit-button"
                  disabled={submitting}
                >
                  {submitting ? "Створення..." : "Створити замовлення"}
                </button>
              </form>
            )}

            {paymentUrl && (
              <div className="payment-box">
                <a href={paymentUrl} target="_blank" rel="noreferrer">
                  Перейти до оплати WayForPay
                </a>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
