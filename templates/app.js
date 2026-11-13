// Tri des tableaux (clic sur un titre de colonne) et filtre des decklists.
(function () {
  function cellValue(cell) {
    var raw = cell.getAttribute("data-sort");
    if (raw === null) raw = cell.textContent.trim();
    var n = Number(raw);
    return raw !== "" && !isNaN(n) ? n : raw.toLowerCase();
  }

  document.querySelectorAll("table.sortable").forEach(function (table) {
    var headers = table.querySelectorAll("thead th");
    headers.forEach(function (th, index) {
      th.classList.add("sortable-col");
      th.tabIndex = 0;
      function sort() {
        var current = th.getAttribute("aria-sort");
        // Premier clic : du plus grand au plus petit pour les nombres.
        var asc = current ? current !== "ascending" : !th.classList.contains("num");
        headers.forEach(function (h) { h.removeAttribute("aria-sort"); });
        th.setAttribute("aria-sort", asc ? "ascending" : "descending");
        var body = table.tBodies[0];
        var rows = Array.prototype.slice.call(body.rows);
        rows.sort(function (a, b) {
          var x = cellValue(a.cells[index]), y = cellValue(b.cells[index]);
          if (x < y) return asc ? -1 : 1;
          if (x > y) return asc ? 1 : -1;
          return 0;
        });
        rows.forEach(function (r) { body.appendChild(r); });
      }
      th.addEventListener("click", sort);
      th.addEventListener("keydown", function (e) { if (e.key === "Enter") sort(); });
    });
  });

  var input = document.getElementById("deck-filter");
  var table = document.getElementById("deck-table");
  if (input && table) {
    input.addEventListener("input", function () {
      var q = input.value.trim().toLowerCase();
      Array.prototype.forEach.call(table.tBodies[0].rows, function (row) {
        row.hidden = q !== "" && row.textContent.toLowerCase().indexOf(q) === -1;
      });
    });
  }
})();
