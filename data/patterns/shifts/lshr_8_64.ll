define i64 @pattern_lshr_8_64(i64 %x) {
entry:
  %result = lshr i64 %x, 8
  ret i64 %result
}
