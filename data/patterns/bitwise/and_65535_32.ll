define i32 @pattern_and_65535_32(i32 %x) {
entry:
  %result = and i32 %x, 65535
  ret i32 %result
}
