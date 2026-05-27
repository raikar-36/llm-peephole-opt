define i32 @pattern_add_65535_32(i32 %x) {
entry:
  %result = add i32 %x, 65535
  ret i32 %result
}
