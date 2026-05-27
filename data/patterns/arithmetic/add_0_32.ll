define i32 @pattern_add_0_32(i32 %x) {
entry:
  %result = add i32 %x, 0
  ret i32 %result
}
