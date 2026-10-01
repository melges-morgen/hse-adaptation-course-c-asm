-- Keep the same bounded table columns in both the course and standalone PDFs.
function Table(tbl)
  local widths = {
    [2] = {0.27, 0.69},
    [4] = {0.12, 0.36, 0.12, 0.36},
    [5] = {0.20, 0.19, 0.19, 0.19, 0.19},
  }
  local selected = widths[#tbl.colspecs]
  if selected then
    for index, column in ipairs(tbl.colspecs) do
      column[2] = selected[index]
      tbl.colspecs[index] = column
    end
  end
  return tbl
end
