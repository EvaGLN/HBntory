/*
Helper shortcut that replaces the long "document.getElementById(id)"
with a quick "$(id)" call throughout the script.
*/
const $ = (id) => document.getElementById(id);

/*
Stores the logged-in user's data (username, role, branch_id) across the entire script once login succeeds;
starts as null while logged out.
*/
let me = null;

/*
Reusable helper that sends an HTTP request to the backend API with optional JSON data,
parses the JSON response, and throws an error if the server fails.
*/
async function call (url, method, body) {
  const r = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined });
  const data = await r.json();
  if (!r.ok) throw new Error(data.error);
  return data;
}

/*
Fetches the latest stock levels for the user's branch,
clears the existing list on screen, and rebuilds it item by item.
*/
async function refresh () {
  const s = await call('/branches/' + me.branch_id + '/stock', 'GET');
  $('stock').textContent = '';
  for (const it of s.products) {
    const li = document.createElement('li');
    li.textContent = it.product_id + ' : ' + it.quantity;
    $('stock').appendChild(li);
  }
}

/*
Sends a request to add or remove stock (depending on "kind") for the selected product and quantity,
then refreshes the list or displays any error message.
*/
async function change (kind) {
  try {
    await call('/branches/' + me.branch_id + '/stock/' + kind, 'POST', { product_id: $('product').value, quantity: Number($('qty').value) });
    $('msg').textContent = '';
    await refresh();
  } catch (e) {
    $('msg').textContent = e.message;
  }
}

/*
Fetches all active users and rebuilds the list on screen (admin only).
*/
async function refreshUsers () {
  const users = await call('/admin/users', 'GET');
  $('users').textContent = '';
  for (const u of users) {
    const li = document.createElement('li');
    li.textContent = u.id + ' : ' + u.username + ' (' + u.role + ', branch ' + u.branch_id + ')';
    $('users').appendChild(li);
  }
}

/*
Sends the admin form to create a new common user,
then reloads the list or displays any error message.
*/
$('new-user').addEventListener('submit', async (e) => {
  e.preventDefault();
  try {
    await call('/admin/users', 'POST', { username: $('nu').value, password: $('np').value, branch_id: Number($('nb').value) });
    $('msg').textContent = '';
    $('new-user').reset();
    await refreshUsers();
  } catch (err) {
    $('msg').textContent = err.message;
  }
});

/*
Handles form submission without reloading the page:
logs the user in, displays their info, and, if they are a "common" user,
populates the product dropdown, reveals the stock dashboard, and loads current stock.
*/
$('login').addEventListener('submit', async (e) => {
  e.preventDefault();
  try {
    me = await call('/login', 'POST', { username: $('u').value, password: $('p').value });
    $('who').textContent = me.username + ' (branch ' + me.branch_id + ')';
    $('msg').textContent = '';
    if (me.role === 'admin') {
      $('admin-ui').hidden = false;
      await refreshUsers();
      return;
    }
    for (const pr of await call('/products', 'GET')) {
      const o = document.createElement('option');
      o.value = pr.sku;
      o.textContent = pr.sku + ' - ' + pr.name;
      $('product').appendChild(o);
    }
    $('stock-ui').hidden = false;
    await refresh();
  } catch (err) {
    $('msg').textContent = err.message;
  }
});

/*
Connect the Add and Remove buttons to the change() function
so clicking them triggers the matching stock update.
*/
$('add').onclick = () => change('add');
$('remove').onclick = () => change('remove');
