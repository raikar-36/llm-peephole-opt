define i64 @pattern_or_65535_64(i64 %x) {
entry:
  %result = or i64 %x, 65535
  ret i64 %result
}
