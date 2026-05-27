define i64 @pattern_shl_31_64(i64 %x) {
entry:
  %result = shl i64 %x, 31
  ret i64 %result
}
