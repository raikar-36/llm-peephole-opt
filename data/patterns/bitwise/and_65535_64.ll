define i64 @pattern_and_65535_64(i64 %x) {
entry:
  %result = and i64 %x, 65535
  ret i64 %result
}
