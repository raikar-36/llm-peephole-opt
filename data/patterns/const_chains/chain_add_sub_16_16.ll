define i32 @chain_add_sub_16_16(i32 %x) {
entry:
  %tmp = add i32 %x, 16
  %result = sub i32 %tmp, 16
  ret i32 %result
}
