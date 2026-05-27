define i64 @pattern_add_128_64(i64 %x) {
entry:
  %result = add i64 %x, 128
  ret i64 %result
}
