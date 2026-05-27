define i64 @pattern_add_0_64(i64 %x) {
entry:
  %result = add i64 %x, 0
  ret i64 %result
}
