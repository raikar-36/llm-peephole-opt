define i32 @pattern_add_neg1_32(i32 %x) {
entry:
  %result = add i32 %x, -1
  ret i32 %result
}
